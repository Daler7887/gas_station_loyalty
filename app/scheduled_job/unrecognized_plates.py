from app.models import FuelSale, PlateRecognition, Car
from app.utils import PLATE_NUMBER_TEMPLATE 
from datetime import datetime, timedelta
import re
from django.db import transaction

def resolve_unrecognized_plates():
    """
    This function is a placeholder for resolving unrecognized plates.
    """
    unrecognized_plate_sales = FuelSale.objects.filter(date__date=datetime.now().date(),plate_recognition__isnull=True, plate_number__isnull=True)
    for sale in unrecognized_plate_sales:
        try:
            print(f"Обрабатываем sale {sale.id} от {sale.date} колонка {sale.pump.name}")
            plate_recog = PlateRecognition.objects.filter(pump=sale.pump, recognized_at__gte=sale.date-timedelta(minutes=15), recognized_at__lte=sale.date+timedelta(minutes=1),is_processed=False, number__regex=PLATE_NUMBER_TEMPLATE).order_by('-recognized_at').first()

            # Если нет подходящих по шаблону, берём последний
            if plate_recog is None:
                plate_recog = PlateRecognition.objects.filter(pump=sale.pump, recognized_at__gte=sale.date-timedelta(minutes=15), recognized_at__lte=sale.date+timedelta(minutes=1), is_processed=False).order_by('-recognized_at').first()

            # Если нет последнего, берём предыдущую продажу
            if plate_recog is None and sale.date.date() == datetime.now().date():
                last_sale = FuelSale.objects.filter(pump=sale.pump, date__gte=sale.date-timedelta(minutes=2), date__lte=sale.date).order_by('-date').first()
                if last_sale:
                    plate_recog = last_sale.plate_recognition

            #Назначаем plate_number
            plate_number = plate_recog.number if plate_recog else None

            #Определяем — новый ли клиент
            new_client = False
            if plate_number and re.match(PLATE_NUMBER_TEMPLATE, plate_number):
                new_client = not Car.objects.filter(plate_number=plate_number).exists()

            #Сохраняем изменения в текущей записи FuelSale
            with transaction.atomic():
                sale.plate_number = plate_number
                sale.plate_recognition = plate_recog
                sale.new_client = new_client
                sale.save()

                if plate_recog:
                    plate_recog.is_processed = True
                    plate_recog.save()

        except Exception as e:
            print(f"Ошибка при обработке sale {sale.id}: {e}")
