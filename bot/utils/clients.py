from bot.models import Bot_user
from bot.utils.bot_functions import bot
from app.utils import PLATE_NUMBER_TEMPLATE
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.services.language_service import get_word_sync
from bot.utils.bot_functions import bot_send_message_sync
import re
import logging

logger = logging.getLogger(__name__)


def inform_user_bonus(user: Bot_user, record_id):
    bonus = user.car.loyalty_points
    if bonus == 0:
        return
    msg = get_word_sync('started fueling', chat_id=user.user_id).format(
        bonus)
    button_text = get_word_sync('use bonus', chat_id=user.user_id)
    buttons = {
        "inline_keyboard": [[{"text": button_text, "callback_data": f'bonus_{record_id}'}]]
    }
    try:
        bot_send_message_sync(
            chat_id=user.user_id,
            text=msg,
            reply_markup=buttons
        )
    except Exception as e:
        logger.error(f"Error sending message to user {user.user_id}: {e}")


def inform_user_sale(car, quantity, final_amount, total_amount, discount, points):
    users = Bot_user.objects.filter(car=car)
    balance = car.loyalty_points
    for user in users:
        if discount == 0:
            msg = get_word_sync('sale success', chat_id=user.user_id).format(
                quantity, final_amount, points, balance)
        else:
            msg = get_word_sync('sale success discount', chat_id=user.user_id).format(
                quantity, total_amount, final_amount, discount, balance)
        try:
            bot_send_message_sync(
                chat_id=user.user_id,
                text=msg
            )
        except Exception as e:
            logger.error(f"Error sending message to user {user.user_id}: {e}")


def inform_changed_balance(car):
    users = Bot_user.objects.filter(car=car)
    for user in users:
        msg = get_word_sync('balance changed', chat_id=user.user_id).format(
            car.loyalty_points
        )
        try:
            bot_send_message_sync(
                chat_id=user.user_id,
                text=msg
            )
        except Exception as e:
            logger.error(f"Error sending message to user {user.user_id}: {e}")


async def validate_plate_number(plate_number: str):
    if re.match(PLATE_NUMBER_TEMPLATE, plate_number):
        return True
    return False
