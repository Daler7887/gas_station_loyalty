from app.models import FuelSale, PlateRecognition
from app.utils import PLATE_NUMBER_TEMPLATE 
from datetime import datetime, timedelta

def resolve_unrecognized_plates():
    """
    This function is a placeholder for resolving unrecognized plates.
    """
    unrecognized_plate_sales = FuelSale.objects.filter(date__date=datetime.now().date(),plate_recognition__isnull=True, plate_number__isnull=True)
    for sale in unrecognized_plate_sales:
        plate_recog = PlateRecognition.objects.filter(pump=sale.pump, recognized_at__gte=sale.date-timedelta(minutes=15), recognized_at__lte=sale.date+timedelta(minutes=1),is_processed=False, number__regex=PLATE_NUMBER_TEMPLATE).order_by('-recognized_at').first()

        # Если нет подходящих по шаблону, берём последний
        if plate_recog is None:
            plate_recog = PlateRecognition.objects.filter(pump=sale.pump, recognized_at__gte=sale.date-timedelta(minutes=15), recognized_at__lte=sale.date+timedelta(minutes=1), is_processed=False).order_by('-recognized_at').first()

        # Если нет последнего, берём предыдущую продажу
        if plate_recog is None and sale.date.date() == datetime.now().date():
            last_sale = FuelSale.objects.filter(pump=sale.pump, date__gte=sale.date-timedelta(minutes=2), date__lte=sale.date).order_by('-date')
            if last_sale:
                plate_recog = last_sale.plate_recognition


