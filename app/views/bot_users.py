from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from bot.models import Bot_user
from app.serializers import BotUserSerializer
from django.db.models import Q


class BotUserListView(APIView):
    def get(self, request):
        search_query = request.query_params.get('search', '')
        paginator = DynamicPageNumberPagination()
        bot_users = Bot_user.objects.filter(
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(car__plate_number__icontains=search_query)
        ).select_related('car').order_by('id')
        result_page = paginator.paginate_queryset(bot_users, request)
        serializer = BotUserSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class DynamicPageNumberPagination(PageNumberPagination):
    page_size = 10  # Значение по умолчанию
    page_size_query_param = 'page_size'  # Клиент может менять размер страницы
    max_page_size = 100  # Максимальное количество записей на странице
