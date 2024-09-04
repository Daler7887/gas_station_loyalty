from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser, BaseParser
from rest_framework_xml.parsers import XMLParser  # Импортируем XML парсер

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
