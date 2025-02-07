from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from app.models import FuelSale
from app.serializers import FuelSaleSerializer


class DynamicPageNumberPagination(PageNumberPagination):
    page_size = 10  # Default value
    page_size_query_param = 'page_size'  # Client can change the page size
    max_page_size = 100  # Maximum number of records per page

class FuelSaleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        paginator = DynamicPageNumberPagination()
        fuel_sales = FuelSale.objects.all().order_by('-date')
        result_page = paginator.paginate_queryset(fuel_sales, request)
        serializer = FuelSaleSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)