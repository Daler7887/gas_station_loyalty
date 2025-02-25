from datetime import datetime, date, timedelta
import requests
import json

PLATE_NUMBER_TEMPLATE = r'^(?!00)(?:\d{2}[A-Za-z]\d{3}[A-Za-z]{2}|\d{5}[A-Za-z]{3}|\d{2}[A-Za-z]\d{6})$'


async def get_user_ip(request):
    x_forwarded_for = await request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = await request.META.get('REMOTE_ADDR')
    return ip


async def datetime_now():
    now = datetime.now()
    return now


async def time_now():
    now = datetime.now()
    return now.time()


async def today():
    today = date.today()
    return today


async def send_request(url, data=None, headers=None, type='get'):
    if type == 'get':
        response = await requests.get(url, params=data, headers=headers)
        content = await json.loads(response.content)
        headers = response.headers
    else:
        response = await requests.post(url, json=data, headers=headers)
        content = await json.loads(response.content)
        headers = response.headers

    return content, headers
