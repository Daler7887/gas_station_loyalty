from telegram import Update
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async
from bot.utils import *
from bot.utils.bot_functions import *
from bot.utils.keyboards import *
from bot.resources.strings import lang_dict
from bot.services import *
from bot.services.language_service import *
from bot.resources.conversationList import *


async def is_message_back(update: Update):
    if update.message.text == await get_word("back", update):
        return True
    else:
        return False


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update = update.callback_query if update.callback_query else update

    bot = context.bot
    keyboards = [
        [
            await get_word('balance', update)
        ],
        [
            await get_word('feedback', update),
            await get_word('settings', update)
        ]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard=keyboards, resize_keyboard=True)
    await bot.send_message(
        update.message.chat_id,
        await get_word('main menu', update),
        reply_markup=reply_markup
    )

    await check_username(update)


@sync_to_async
def filter_objects_sync(model_class, filters, exclude):
    query = model_class.objects.filter(**filters)
    if exclude is not None:
        query = query.exclude(**exclude)
    return list(query.values())