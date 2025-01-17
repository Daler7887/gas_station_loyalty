from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InputMediaPhoto,
    InputMedia,
    ReplyKeyboardRemove,
    Bot,
    Update
)
from telegram.constants import (
    ParseMode, 
    ChatAction,
)
from telegram.ext import (
    ConversationHandler,
    ContextTypes
)
from uuid import uuid4
from config import BOT_API_TOKEN

bot = Bot(BOT_API_TOKEN)

async def update_message_reply_text(update: Update, text, reply_markup=None, disable_web_page_preview = True):
    message = await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode = ParseMode.HTML,
        disable_web_page_preview = disable_web_page_preview,
    )
    return message

async def bot_send_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text, reply_markup=None, disable_web_page_preview = True):
    bot = context.bot
    message = await bot.send_message(
        update.message.chat.id, 
        text,
        reply_markup=reply_markup,
        parse_mode = ParseMode.HTML,
        disable_web_page_preview = disable_web_page_preview,
        )
    return message

async def bot_send_document(update: Update, context: ContextTypes.DEFAULT_TYPE, document, reply_markup=None, caption=None):
    bot = context.bot
    message = await bot.send_document(
        update.message.chat.id,
        document,
        caption=caption,
        reply_markup=reply_markup,
        parse_mode = ParseMode.HTML,
    )
    return message

async def send_newsletter(bot: Bot, chat_id, text, photo=None, video=None, document=None, reply_markup=None, pin_message=False):
    try:
        if not (photo or video or document):
            # send text message
            message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        
        if photo:
            # send photo
            message = await bot.send_photo(
                chat_id,
                photo,
                caption=text,
                reply_markup=reply_markup,
                parse_mode = ParseMode.HTML,
            )

        if video:
            # send video
            message = await bot.send_video(
                chat_id,
                video,
                caption=text,
                reply_markup=reply_markup,
                parse_mode = ParseMode.HTML,
            )
        if document:
            # send document
            message = await bot.send_document(
                chat_id,
                document,
                caption=text,
                reply_markup=reply_markup,
                parse_mode = ParseMode.HTML,
            )

        if pin_message:
            await bot.pin_chat_message(chat_id=chat_id, message_id=message.message_id)
        return message
    except:
        return None

async def bot_delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE, message_id=None):
    if not message_id:
        message_id = update.message.message_id
    bot = context.bot
    try:
        await bot.delete_message(update.message.chat.id, message_id)
    except:
        return

async def bot_send_and_delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text, reply_markup=None):
    bot = context.bot
    message = await bot.send_message(
        update.message.chat.id, 
        text,
        reply_markup=reply_markup,
        parse_mode = ParseMode.HTML
        )
    await bot.delete_message(update.message.chat.id, message.message_id)
    return

async def bot_edit_message_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text, msg_id=None):
    bot = context.bot
    if not msg_id:
        msg_id = update.message.message_id
    await bot.edit_message_text(
        chat_id=update.message.chat.id,
        message_id=msg_id,
        text=text, 
        parse_mode=ParseMode.HTML
    )

async def bot_edit_message_reply_markup(update: Update, context: ContextTypes.DEFAULT_TYPE, msg_id=None, reply_markup=None):
    bot = context.bot
    if not msg_id:
        msg_id = update.message.message_id
    await bot.edit_message_reply_markup(
        chat_id=update.message.chat.id,
        message_id=msg_id,
        reply_markup=reply_markup
    )

async def reply_keyboard_markup(keyboard=[], resize_keyboard=True, one_time_keyboard=False):
    markup = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=resize_keyboard,
        one_time_keyboard=one_time_keyboard
    )
    return markup

async def reply_keyboard_remove():
    markup = ReplyKeyboardRemove(True)
    return markup


async def inlinequeryresultarticle(title, description=None, title_id=None):
    message_content = title
    if title_id:
        message_content = '{}<>?{}'.format(title, title_id)

    article = InlineQueryResultArticle(
        id=str(uuid4()),
        title=title,
        description = description,
        input_message_content=InputTextMessageContent(message_content),
    )
    return article

async def update_inline_query_answer(update: Update, article):
    await update.inline_query.answer(article, auto_pagination=True, cache_time=120)

async def bot_answer_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE, text, show_alert=True):
    bot = context.bot
    await bot.answer_callback_query(callback_query_id=update.id, text=text, show_alert=show_alert)

async def bot_send_chat_action(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_action=ChatAction.TYPING):
    bot = context.bot
    await bot.sendChatAction(update.message.chat.id, chat_action)

async def send_media_group(bot: Bot, chat_id, photos):

    all = [InputMediaPhoto(photo.file) for photo in photos.all()]
    try:
        await bot.send_media_group(chat_id = chat_id, media = all)
    except:
        w=0