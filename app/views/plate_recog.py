from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from app.models import PlateRecognition, Pump, FuelSale
from app.utils.alpr import read_plate
import xmltodict
import base64
from bot.utils.clients import inform_user_bonus
from bot.models import Bot_user
import json
import logging

logger = logging.getLogger(__name__)


class PlateRecognitionView(APIView):
    # parser_classes = (MultiPartParser, FormParser, )
    permission_classes = [AllowAny]  # Отключаем авторизацию

    def post(self, request, format=None):
            # return Response(status=status.HTTP_200_OK)
            # serializer = CameraDataSerializer(data=request.data)
        try:
            if "parkingSpaceDetection" not in request.data.keys():
                return Response(status=status.HTTP_200_OK)

            event = json.loads(request.data['parkingSpaceDetection'])

            image_path = None
            image_path1 = None

            if "backgroundImage" in request.data.keys():
                background_image = request.data['backgroundImage']
                background_image_name = f'car_images/{background_image.name}.jpg'
                image_path = default_storage.save(background_image_name, ContentFile(background_image.read()))


            # plate_number = recognize_plate(base64_image)
            # plate_number = read_plate(image_path1).upper()

            pump = Pump.objects.filter(ip_address=event['ipAddress']).first()
            record_exists = PlateRecognition.objects.filter(
                pump=pump, recognized_at=event['dateTime'][:19]).exists()

            if record_exists:
                return Response(status=status.HTTP_200_OK)

            # plate_number = recognize_plate(base64_image)
            plate_number = event['PackingSpaceRecognition'][0]['plateNo']
            if pump and pump.alpr and "vehicleBodyImage" in request.data.keys():
                vehicle_body_image = request.data['vehicleBodyImage']
                vehicle_body_image_name = f'car_images/{vehicle_body_image.name}.jpg'
                image_path1 = default_storage.save(vehicle_body_image_name, ContentFile(vehicle_body_image.read()))
                plate_number = read_plate(image_path1).upper()

            event_type = event['PackingSpaceRecognition'][0]['vehicleEnterState']
            if event_type == 'enter':
                new_record = PlateRecognition(
                    pump=pump,
                    number=plate_number,
                    image1=image_path,
                    recognized_at=event['dateTime'][:19]
                )
                new_record.save()
            else:
                record = PlateRecognition.objects.filter(
                    pump=pump,exit_time=None, recognized_at__lte=event['dateTime'][:19]).first()
                if not record:
                    return Response(status=status.HTTP_200_OK)
                record.image2 = image_path
                record.exit_time = event['dateTime'][:19]
                record.save()
                fuel_sale = FuelSale.objects.filter(plate_recognition__isnull=True, created_at__lte=record.exit_time, created_at__gte=record.recognized_at).first()
                if fuel_sale:
                    fuel_sale.plate_recognition = record
                    fuel_sale.save()

        except Exception as e:
            logger.error(f"Internal Server Error: {e}")
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            users = Bot_user.objects.filter(car__plate_number=plate_number)
            for user in users:
                inform_user_bonus(user)
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления: {e} \n Plate number: {plate_number}")

        return Response(status=status.HTTP_200_OK)


def convert_inmemoryfile_to_base64(uploaded_file):
    # Прочитайте содержимое файла
    file_data = uploaded_file.read()

    # Преобразуйте бинарные данные в строку Base64
    base64_encoded_file = base64.b64encode(file_data).decode('utf-8')

    return base64_encoded_file
