from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser, BaseParser
from rest_framework_xml.parsers import XMLParser  # Импортируем XML парсер
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
import urllib.parse


class ContentTypeParserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        content_type = request.content_type

        if content_type == 'application/json':
            request.data = JSONParser().parse(request)
        elif content_type == 'application/x-www-form-urlencoded':
            request.data = FormParser().parse(request)
        elif content_type == 'multipart/form-data':
            request.data = MultiPartParser().parse(request)
        elif content_type == 'application/xml':
            request.data = XMLParser().parse(request)  # Добавляем поддержку XML

\
User = get_user_model()

@database_sync_to_async
def get_user_from_token(token):
    try:
        validated_token = AccessToken(token)
        user_id = validated_token['user_id']
        user = User.objects.get(id=user_id)
        return user
    except Exception:
        return None

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope['query_string'].decode()
        params = dict(urllib.parse.parse_qsl(query_string))
        token = params.get('token', None)
        scope['user'] = AnonymousUser()

        if token:
            user = await get_user_from_token(token)
            if user:
                scope['user'] = user

        return await super().__call__(scope, receive, send)
