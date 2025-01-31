from bot.models import Bot_user
from bot.utils.bot_functions import bot
from asgiref.sync import async_to_sync
from bot.services.language_service import get_word 
import re


def inform_user_bonus(user: Bot_user):
    bonus = user.car.loyalty_points
    msg = async_to_sync(get_word)('started fueling', chat_id=user.user_id).format(
        bonus)
    async_to_sync(bot.send_message)(
        chat_id=user.user_id,
        text=msg,
        parse_mode="HTML"
    )


async def validate_plate_number(plate_number: str):
    # Проверяем, есть ли в базе данных пользователь с таким номером
    if re.match(r'^[A-Z0-9]{4,10}', plate_number):
        return True
    return False
