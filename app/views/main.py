from app.views import *
import os
from core.settings import BASE_DIR
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from app.models import FuelSale, LoyaltyPointsTransaction
from django.db.models import Sum, Avg, Count
from django.utils import timezone


def get_file(request, path):
    file = open(os.path.join(BASE_DIR, f'files/{path}'), 'rb')
    return FileResponse(file)


class DashboardData(APIView):
    def get(self, request):
        current_month = timezone.now().month
        last_month = (timezone.now().replace(day=1) - timezone.timedelta(days=1)).month

        sales_query = FuelSale.objects.filter(date__month=current_month)
        last_month_sales_query = FuelSale.objects.filter(date__month=last_month)
        new_customers_query = FuelSale.objects.filter(date__month=current_month, new_client=True)
        last_month_new_customers_query = FuelSale.objects.filter(date__month=last_month, new_client=True)
        bonuses_earned_query = LoyaltyPointsTransaction.objects.filter(transaction_type='accrual', created_at__month=current_month)
        last_month_bonuses_earned_query = LoyaltyPointsTransaction.objects.filter(transaction_type='accrual', created_at__month=last_month)
        bonuses_spent_query = LoyaltyPointsTransaction.objects.filter(transaction_type='redeem', created_at__month=current_month)
        last_month_bonuses_spent_query = LoyaltyPointsTransaction.objects.filter(transaction_type='redeem', created_at__month=last_month)

        sales = sales_query.aggregate(total=Sum('total_amount'))
        last_month_sales = last_month_sales_query.aggregate(total=Sum('total_amount'))
        new_customers = new_customers_query.aggregate(total=Count('new_client'))
        last_month_new_customers = last_month_new_customers_query.aggregate(total=Count('new_client'))
        bonuses_earned = bonuses_earned_query.aggregate(total=Sum('points'))
        last_month_bonuses_earned = last_month_bonuses_earned_query.aggregate(total=Sum('points'))
        bonuses_spent = bonuses_spent_query.aggregate(total=Sum('points'))
        last_month_bonuses_spent = last_month_bonuses_spent_query.aggregate(total=Sum('points'))

        sales_percent = ((sales['total'] or 0) - (last_month_sales['total'] or 0)) / (last_month_sales['total'] or 1) * 100
        new_customers_percent = ((new_customers['total'] or 0) - (last_month_new_customers['total'] or 0)) / (last_month_new_customers['total'] or 1) * 100
        bonuses_earned_percent = ((bonuses_earned['total'] or 0) - (last_month_bonuses_earned['total'] or 0)) / (last_month_bonuses_earned['total'] or 1) * 100
        bonuses_spent_percent = ((bonuses_spent['total'] or 0) - (last_month_bonuses_spent['total'] or 0)) / (last_month_bonuses_spent['total'] or 1) * 100

        data = {
            "sales": {
                "total": sales['total'] or 0,
                "percent": sales_percent,
                "series": list(sales_query.values('date__month').annotate(total=Sum('total_amount')).order_by('date__month'))   
            },
            "newCustomers": {
                "total": new_customers['total'] or 0,
                "percent": new_customers_percent,
                "series": list(FuelSale.objects.values('date__month').annotate(total=Count('new_client')).order_by('date__month'))
            },
            "bonusesEarned": {
                "total": bonuses_earned['total'] or 0,
                "percent": bonuses_earned_percent,
                "series": list(LoyaltyPointsTransaction.objects.filter(transaction_type='accrual').values('created_at__month').annotate(total=Sum('points')).order_by('created_at__month'))
            },
            "bonusesSpent": {
                "total": bonuses_spent['total'] or 0,
                "percent": bonuses_spent_percent,
                "series": list(LoyaltyPointsTransaction.objects.filter(transaction_type='redeem').values('created_at__month').annotate(total=Sum('points')).order_by('created_at__month'))
            }
        }

        return Response(data, status=status.HTTP_200_OK)
