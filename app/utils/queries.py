from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from app.models import FuelSale, LoyaltyPointsTransaction
from django.contrib.admin.models import LogEntry
from django.db.models import OuterRef, Subquery
from app.models import Pump, PlateRecognition
from channels.db import database_sync_to_async
from datetime import datetime, timedelta, date
import re
from app.models import Car


PLATE_NUMBER_TEMPLATE = r'^(?:\d{2}[A-Za-z]\d{3}[A-Za-z]{2}|\d{5}[A-Za-z]{3}|\d{2}[A-Za-z]\d{6})$'


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
        recognized_at__gt=datetime.now()-timedelta(minutes=15),
        number__regex=PLATE_NUMBER_TEMPLATE
    ).order_by('-recognized_at')

    pumps_qs = Pump.objects.all().annotate(
        last_plate_number=Subquery(
            last_plate_recognition_qs.values('number')[:1]),
        last_plate_recognized_at=Subquery(
            last_plate_recognition_qs.values('recognized_at')[:1]),
        use_bonus=Subquery(last_plate_recognition_qs.values('use_bonus')[:1])
    ).values('id', 'number', 'organization__name', 'last_plate_number', 'last_plate_recognized_at', 'use_bonus').order_by('number')

    pump_info = []
    for pump in pumps_qs:
        # For each pump, query the last fuel sale where sale date is >= plate recognition's recognized_at
        fuel_sale = None
        if pump['last_plate_recognized_at']:
            fuel_sale = FuelSale.objects.filter(
                pump_id=pump['id'],
                date__gte=pump['last_plate_recognized_at']  
            ).order_by('-date').first()
        else:
            fuel_sale = FuelSale.objects.filter(
                pump_id=pump['id'],
            ).order_by('-date').first()
        # Get car info if exists
        car = Car.objects.filter(plate_number=pump['last_plate_number']).first(
        ) if pump['last_plate_number'] else None

        pump_info.append({
            'pumpNumber': pump['number'],
            'organization': pump['organization__name'],
            'plateNumber': pump['last_plate_number'],
            'plateRecognized_at': pump['last_plate_recognized_at'].strftime('%Y-%m-%d %H:%M:%S') if pump['last_plate_recognized_at'] else None,
            'userBalance': car.loyalty_points if car else 0,
            'useBonus': pump['use_bonus'] if pump['use_bonus'] else False,
            'newClient': True if pump['last_plate_number'] and not car else False,
            'quantity': float(fuel_sale.quantity) if fuel_sale and fuel_sale.quantity else 0,
            'discount': float(fuel_sale.discount_amount) if fuel_sale and fuel_sale.discount_amount else 0,
            'finalAmount': float(fuel_sale.final_amount) if fuel_sale and fuel_sale.final_amount else 0,
            'totalAmount': float(fuel_sale.total_amount) if fuel_sale and fuel_sale.total_amount else 0,
            'price': float(fuel_sale.price) if fuel_sale and fuel_sale.price else 0,
        })

    return pump_info
