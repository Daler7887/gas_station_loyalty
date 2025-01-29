from django.db.models import Sum
from bot.models import Bot_user
from bot.utils.bot_functions import bot_send_message
from asgiref.sync import async_to_sync
import re


def inform_user_bonus(user: Bot_user):
    bonus = user.car.loyalty_points
    msg = "Начался процесс заправки вашего автомобиля. На вашем балансе бонус в размере {} сум".format(
        bonus)
    bot_send_message(user.user_id, msg)


async def validate_plate_number(plate_number: str):
    # Проверяем, есть ли в базе данных пользователь с таким номером
    if re.match(r'^[A-Z0-9]{4,10}', plate_number):
        return True
    return False
