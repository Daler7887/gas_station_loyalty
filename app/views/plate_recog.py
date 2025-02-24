from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from app.models import PlateRecognition, Pump
from app.utils.alpr import read_plate
import xmltodict
import base64
from bot.utils.clients import inform_user_bonus
from bot.models import Bot_user
from app.utils.queries import PLATE_NUMBER_TEMPLATE
import re
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PlateRecognitionView(APIView):
    # parser_classes = (MultiPartParser, FormParser, )
    permission_classes = [AllowAny]  # Отключаем авторизацию

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

        # plate_number = recognize_plate(base64_image)
        # plate_number = read_plate(image_path1).upper()

        pump = Pump.objects.filter(ip_address=event['ipAddress']).first()
        record_exists = PlateRecognition.objects.filter(
            pump=pump, recognized_at=event['dateTime'][:19]).exists()

        if record_exists:
            return Response(status=status.HTTP_200_OK)

        # plate_number = recognize_plate(base64_image)
        plate_number = event['ANPR']['licensePlate']
        if pump and not re.match(PLATE_NUMBER_TEMPLATE, plate_number):
            plate_number = read_plate(image_path)

        timestamp = datetime.strptime(
            event['dateTime'][:19], '%Y-%m-%dT%H:%M:%S')
        same_plate = PlateRecognition.objects.filter(
            pump=pump, number=plate_number, recognized_at__gte=timestamp-timedelta(minutes=15)).exists()
        if same_plate:
            return Response(status=status.HTTP_200_OK)

        new_record = PlateRecognition(
            pump=pump,
            number=plate_number,
            image1=image_path,
            image2=image_path1,
            recognized_at=timestamp,
        )
        new_record.save()

        try:
            users = Bot_user.objects.filter(car__plate_number=plate_number)
            for user in users:
                inform_user_bonus(user)
        except Exception as e:
            logger.error(
                f"Ошибка при отправке уведомления: {e} \n Plate number: {plate_number}")

        return Response(status=status.HTTP_200_OK)


def convert_inmemoryfile_to_base64(uploaded_file):
    # Прочитайте содержимое файла
    file_data = uploaded_file.read()

    # Преобразуйте бинарные данные в строку Base64
    base64_encoded_file = base64.b64encode(file_data).decode('utf-8')

    return base64_encoded_file
