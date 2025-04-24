from app.views import *
import os
from core.settings import BASE_DIR
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from app.utils.queries import get_year_sales, get_new_customers, get_bonuses_earned, get_bonuses_spent, get_logs, get_customer_share
from rest_framework.permissions import IsAuthenticated
from app.serializers import UserSerializer


def get_file(request, path):
    file = open(os.path.join(BASE_DIR, f'files/{path}'), 'rb')
    return FileResponse(file)


class DashboardData(APIView):
    def get(self, request):
        # sales data
        year_sales = get_year_sales()
        sales_month_count = year_sales.count()
        this_month_sales = year_sales.last().get('total', 0) if sales_month_count > 0 else 0
        sales_increase_percent = 0

        if sales_month_count > 1:
            last_month_sales = year_sales[sales_month_count -
                                          2].get('total', 0)
            sales_increase_percent = (
                (this_month_sales - last_month_sales) / last_month_sales) * 100

        # new customers data
        new_customers = get_new_customers()
        new_customers_count = new_customers.count()
        this_month_new_customers = new_customers.last().get('total', 0) if new_customers_count > 0 else 0
        new_customers_percent = 0
        if new_customers_count > 1:
            last_month_new_customers = new_customers[new_customers_count - 2].get(
                'total', 0)
            new_customers_percent = (
                (this_month_new_customers - last_month_new_customers) / last_month_new_customers) * 100

        # bonuses data
        bonuses_earned = get_bonuses_earned()
        bonuses_earned_count = bonuses_earned.count()
        this_month_bonuses_earned = bonuses_earned.last().get('total', 0) if bonuses_earned_count > 0 else 0
        bonuses_earned_percent = 0
        if bonuses_earned_count > 1:
            last_month_bonuses_earned = bonuses_earned[bonuses_earned_count - 2].get(
                'total', 0)
            bonuses_earned_percent = (
                (this_month_bonuses_earned - last_month_bonuses_earned) / last_month_bonuses_earned) * 100

        bonuses_spent = get_bonuses_spent()
        bonuses_spent_count = bonuses_spent.count()
        this_month_bonuses_spent = bonuses_spent.last().get('total', 0) if bonuses_spent_count > 0 else 0
        bonuses_spent_percent = 0
        if bonuses_spent_count > 1:
            last_month_bonuses_spent = bonuses_spent[bonuses_spent_count - 2].get(
                'total', 0)
            bonuses_spent_percent = (
                (this_month_bonuses_spent - last_month_bonuses_spent) / last_month_bonuses_spent) * 100

        data = {
            "sales": {
                "total": this_month_sales,
                "percent": sales_increase_percent,
                "series": year_sales
            },
            "newCustomers": {
                "total": this_month_new_customers,
                "percent": new_customers_percent,
                "series": new_customers
            },
            "bonusesEarned": {
                "total": this_month_bonuses_earned,
                "percent": bonuses_earned_percent,
                "series": bonuses_earned
            },
            "bonusesSpent": {
                "total": this_month_bonuses_spent,
                "percent": bonuses_spent_percent,
                "series": bonuses_spent
            },
            "logs": get_logs(request.user),
            "customer_share": get_customer_share()
        }

        return Response(data, status=status.HTTP_200_OK)


class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)