from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from app.models import FuelSale, LoyaltyPointsTransaction
from django.contrib.admin.models import LogEntry
from django.db.models import OuterRef, Subquery
from app.models import Pump, PlateRecognition
from channels.db import database_sync_to_async
from datetime import datetime, timedelta, date
from app.models import Car
from app.utils import PLATE_NUMBER_TEMPLATE
from django.db import connection

def get_year_sales():
    today = date.today()
    # Находим первый день текущего месяца
    start_of_current_month = today.replace(day=1)
    # Вычисляем начало периода:
    #    - минус 11 месяцев от начала текущего месяца,
    start_date = start_of_current_month - relativedelta(months=11)

    # Конец периода = последний день текущего месяца
    end_of_current_month = (start_of_current_month
                            + relativedelta(months=1)
                            - relativedelta(days=1))

    # Пример запроса к модели Sale (поменяйте под свои поля/модель):
    queryset = (
        FuelSale.objects
        .filter(date__gte=start_date, date__lte=end_of_current_month)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )

    return queryset


def get_new_customers():
    today = date.today()
    # Находим первый день текущего месяца
    start_of_current_month = today.replace(day=1)
    # Вычисляем начало периода:
    #    - минус 11 месяцев от начала текущего месяца,
    start_date = start_of_current_month - relativedelta(months=11)
    end_of_current_month = (start_of_current_month
                            + relativedelta(months=1)
                            - relativedelta(days=1))

    queryset = (
        FuelSale.objects
        .filter(date__gte=start_date, date__lte=end_of_current_month, new_client=True)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )

    return queryset


def get_customer_share():
    if connection.vendor == 'sqlite':
        date_filter = "datetime('now', '-60 days')"
    elif connection.vendor == 'postgresql':
        date_filter = "NOW() - interval '60 days'"
    else:
        raise Exception("Unsupported database backend")

    query = f"""
        WITH total_sales AS (
          SELECT COUNT(*) AS total
          FROM app_fuelsale
          WHERE date >= {date_filter}
        ),
        one_time_sales AS (
          SELECT COUNT(*) AS one_time
          FROM app_fuelsale f
          WHERE f.new_client = TRUE
            AND f.date >= {date_filter}
            AND (
              SELECT COUNT(*) FROM app_fuelsale
              WHERE plate_number = f.plate_number
                AND date >= {date_filter}
            ) = 1
        )
        SELECT
          o.one_time,
          t.total - o.one_time AS regular
        FROM total_sales t, one_time_sales o;
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        row = cursor.fetchone() or (0, 0)
        return {
            'one_time': row[0] or 0,
            'regular': row[1] or 0
        }


def get_bonuses_earned():
    today = date.today()
    # Находим первый день текущего месяца
    start_of_current_month = today.replace(day=1)
    # Вычисляем начало периода:
    #    - минус 11 месяцев от начала текущего месяца,
    start_date = start_of_current_month - relativedelta(months=11)
    end_of_current_month = (start_of_current_month
                            + relativedelta(months=1)
                            - relativedelta(days=1))

    queryset = (
        LoyaltyPointsTransaction.objects
        .filter(created_at__gte=start_date, created_at__lte=end_of_current_month, transaction_type='accrual')
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('points'))
        .order_by('month')
    )

    return queryset


def get_bonuses_spent():
    today = date.today()
    # Находим первый день текущего месяца
    start_of_current_month = today.replace(day=1)
    # Вычисляем начало периода:
    #    - минус 11 месяцев от начала текущего месяца,
    start_date = start_of_current_month - relativedelta(months=11)
    end_of_current_month = (start_of_current_month
                            + relativedelta(months=1)
                            - relativedelta(days=1))

    queryset = (
        LoyaltyPointsTransaction.objects
        .filter(created_at__gte=start_date, created_at__lte=end_of_current_month, transaction_type='redeem')
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('points'))
        .order_by('month')
    )

    return queryset


def get_logs(user):
    actions_color = {
        1: 2,
        2: 4,
        3: 5,
    }
    if user.is_superuser:
        logs = LogEntry.objects.all().order_by('-action_time')[:5]
    else:
        logs = LogEntry.objects.filter(user=user).order_by('-action_time')[:5]
    data = [
        {
            "user": log.user.username,
            "action_time": log.action_time.strftime("%Y-%m-%d %H:%M:%S"),
            "object_repr": log.object_repr,
            "action_id": actions_color[log.action_flag],
        }
        for log in logs
    ]
    return data


@database_sync_to_async
def aget_pump_info():
    return get_pump_info()


def get_pump_info():
    # Get pumps with last plate recognition (subquery)
    last_plate_recognition_qs = PlateRecognition.objects.filter(
        pump=OuterRef('pk'),
        recognized_at__gt=datetime.now()-timedelta(minutes=10),
        number__regex=PLATE_NUMBER_TEMPLATE,
        is_processed=False,
    ).order_by('-recognized_at')

    last_fuel_sale = FuelSale.objects.filter(
        pump=OuterRef('id'),
        date__gt=datetime.now() - timedelta(minutes=5)
    ).order_by('-date')

    pumps_qs = Pump.objects.all().annotate(
        last_plate_recognition_id=Subquery(
            last_plate_recognition_qs.values('id')[:1]),
        last_plate_recognized_at=Subquery(
            last_plate_recognition_qs.values('recognized_at')[:1]),
        last_plate_number=Subquery(
            last_plate_recognition_qs.values('number')[:1]),
        last_plate_use_bonus=Subquery(
            last_plate_recognition_qs.values('use_bonus')[:1]),
        sales_plate_recognition_id=Subquery(
            last_fuel_sale.values('plate_recognition_id')[:1]),
        sales_plate_recognized_at=Subquery(
            last_fuel_sale.values('plate_recognition__recognized_at')[:1]),
        sales_plate_number=Subquery(
            last_fuel_sale.values('plate_recognition__number')[:1]),
        sales_plate_use_bonus=Subquery(
            last_fuel_sale.values('plate_recognition__use_bonus')[:1]),
        sales_date=Subquery(last_fuel_sale.values('date')[:1]),
        price=Subquery(last_fuel_sale.values('price')[:1]),
        quantity=Subquery(last_fuel_sale.values('quantity')[:1]),
        discount=Subquery(last_fuel_sale.values('discount_amount')[:1]),
        final_amount=Subquery(last_fuel_sale.values('final_amount')[:1]),
        total_amount=Subquery(last_fuel_sale.values('total_amount')[:1]),
    ).values(
        'id',
        'number',
        'organization__name',
        'last_plate_recognition_id',
        'last_plate_recognized_at',
        'last_plate_number',
        'last_plate_use_bonus',
        'sales_plate_recognition_id',
        'sales_plate_recognized_at',
        'sales_plate_number',
        'sales_plate_use_bonus',
        'sales_date',
        'price',
        'quantity',
        'total_amount',
        'discount',
        'final_amount',
    ).order_by('number')

    pump_info = []
    for pump in pumps_qs:
        prefix = 'sales_' if pump['sales_plate_recognition_id'] else 'last_'
        new_drive_in = pump['sales_plate_recognition_id'] is None
        if pump['last_plate_recognition_id'] and pump['sales_plate_recognition_id'] and pump['sales_date'] < pump['last_plate_recognized_at']:
            prefix = 'last_'
            new_drive_in = True

        # Get car info if exists
        car = Car.objects.filter(
            plate_number=pump[f'{prefix}plate_number']).first()

        pump_info.append({
            'pumpNumber': pump['number'],
            'organization': pump['organization__name'],
            'plateNumber': pump[f'{prefix}plate_number'],
            'plateRecognized_at': pump[f'{prefix}plate_recognized_at'].strftime('%Y-%m-%d %H:%M:%S') if pump[f'{prefix}plate_recognized_at'] else None,
            'userBalance': car.loyalty_points if car else 0,
            'useBonus': pump[f'{prefix}plate_use_bonus'] if pump[f'{prefix}plate_use_bonus'] else False,
            'newClient': True if pump[f'{prefix}plate_number'] and car is None else False,
            'quantity': float(pump['quantity']) if pump['quantity'] and not new_drive_in else 0,
            'discount': float(pump['discount']) if pump['discount'] and not new_drive_in else 0,
            'finalAmount': float(pump['final_amount']) if pump['final_amount'] and not new_drive_in else 0,
            'totalAmount': float(pump['total_amount']) if pump['total_amount'] and not new_drive_in else 0,
            'price': float(pump['price']) if pump['price'] and not new_drive_in else 0,
        })

    return pump_info
