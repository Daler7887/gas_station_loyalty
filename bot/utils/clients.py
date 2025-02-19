from bot.models import Bot_user
from bot.utils.bot_functions import bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup 
from asgiref.sync import async_to_sync
from bot.services.language_service import get_word 
import re


def inform_user_bonus(user: Bot_user, record_id):
    bonus = user.car.loyalty_points
    if bonus == 0:
        return
    msg = async_to_sync(get_word)('started fueling', chat_id=user.user_id).format(
        bonus)
    button_text = async_to_sync(get_word)('use bonus', chat_id=user.user_id)
    buttons = [[InlineKeyboardButton(button_text, callback_data=f'bonus_{record_id}')]]
    async_to_sync(bot.send_message)(
        chat_id=user.user_id,
        text=msg,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def validate_plate_number(plate_number: str):
    # Проверяем, есть ли в базе данных пользователь с таким номером
    if re.match(r'^(?:\d{2}[A-Za-z]\d{3}[A-Za-z]{2}|\d{5}[A-Za-z]{3}|\d{2}[A-Za-z]\d{6})$', plate_number):
        return True
    return False
