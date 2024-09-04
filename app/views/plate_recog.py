from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from app.utils.open_ai import recognize_plate
from app.models import PlateRecognition, Pump
import xmltodict
import base64

class PlateRecognitionView(APIView):
    # parser_classes = (MultiPartParser, FormParser, )

    def post(self, request, format=None):
        # return Response(status=status.HTTP_200_OK)
        # serializer = CameraDataSerializer(data=request.data)
        if "anpr.xml" not in request.data.keys():
            return Response(status=status.HTTP_200_OK)    
        parsed_data = xmltodict.parse(request.data["anpr.xml"])

        event = parsed_data['EventNotificationAlert']

        image_path = None
        image_path1 = None
        pictures_list = event['ANPR']['pictureInfoList']['pictureInfo']

        if type(pictures_list) == dict:
            image_path = request.data[pictures_list['fileName']]
        elif len(pictures_list) > 0:
            image_path = request.data[pictures_list[0]['fileName']]
        if len(pictures_list) > 1:
            image_path1 = request.data[pictures_list[1]['fileName']]
        
        # base64_image = convert_inmemoryfile_to_base64(image_path)
        # plate_number = recognize_plate(base64_image)
        pump = Pump.objects.filter(ip_address=event['ipAddress']).first()
        record_exists = PlateRecognition.objects.filter(pump=pump, recognized_at=event['dateTime'][:19]).exists()

        if record_exists:
            return Response(status=status.HTTP_200_OK)
        
        # plate_number = recognize_plate(base64_image)
       
        new_record = PlateRecognition(
            pump = pump,
            number = event["ANPR"]['licensePlate'],
            image1 = image_path,
            image2 = image_path1,
            recognized_at = event['dateTime'][:19]
        )
        new_record.save()
        return Response(status=status.HTTP_200_OK)
    

def convert_inmemoryfile_to_base64(uploaded_file):
    # Прочитайте содержимое файла
    file_data = uploaded_file.read()
    
    # Преобразуйте бинарные данные в строку Base64
    base64_encoded_file = base64.b64encode(file_data).decode('utf-8')
    
    return base64_encoded_file


