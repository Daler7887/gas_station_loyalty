from app.models import FuelSale, PlateRecognition, Car
from app.utils import PLATE_NUMBER_TEMPLATE 
from datetime import datetime, timedelta
import re
from django.db import transaction

def resolve_unrecognized_plates():
    """
    This function is a placeholder for resolving unrecognized plates.
    """
    unrecognized_plate_sales = FuelSale.objects.filter(date__gte=datetime.now()-timedelta(days=2),
                                                       plate_recognition__isnull=True, plate_number__isnull=True, total_amount__gte=2000)
    for sale in unrecognized_plate_sales:
        try:
            if sale.total_amount < 2000:
                print(f"Пропускаем sale {sale.id} с суммой {sale.total_amount} меньше 2000")
                continue
            print(f"Обрабатываем sale {sale.id} от {sale.date} колонка {sale.pump.number}")
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

            print(f"Найдено plate_recog: {plate_recog} с номером {plate_number}, новый клиент: {new_client}")
            #Сохраняем изменения в текущей записи FuelSale
            with transaction.atomic():
                sale.plate_number = plate_number
                sale.plate_recognition = plate_recog
                sale.new_client = new_client
                sale.save()
                print(f"Обновлено sale {sale.id}: plate_number={sale.plate_number}, new_client={sale.new_client}")

                if plate_recog:
                    plate_recog.is_processed = True
                    plate_recog.save()
                print(f"Обновлено plate_recog {plate_recog.id} как обработанное.")

            print(f"Обработано sale {sale.id}: plate_number={sale.plate_number}, new_client={sale.new_client}")

        except Exception as e:
            print(f"Ошибка при обработке sale {sale.id}: {e}")
