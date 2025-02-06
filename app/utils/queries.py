import datetime
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from app.models import FuelSale, LoyaltyPointsTransaction


def get_year_sales():
    today = datetime.date.today()
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
    today = datetime.date.today()
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
    today = datetime.date.today()
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
    today = datetime.date.today()
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