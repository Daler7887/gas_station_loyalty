from telegram import Update
from telegram.ext import ConversationHandler
from bot.services.language_service import get_word
from bot.bot import *
from config import TG_GROUP_ID


async def handle_suggestions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup([[await get_word('back', update)]], resize_keyboard=True)
    await update.message.reply_text(
        await get_word('send suggestions', update), reply_markup=keyboard
    )
    return GET_SUGGESTION


async def receive_suggestions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_message_back(update):
        await main_menu(update, context)
        return ConversationHandler.END

    text = ''
    if update.message.text:
        text = update.message.text
    if update.message.caption:
        text = update.message.caption

    message_id = update.message.message_id
    obj = await get_object_by_user_id(user_id=update.message.chat.id)

    text = f"{text}\n\nОтзыв от @{update.message.from_user.username}:\nНомер телефона: {obj.phone}\nНомер машины: {obj.car.plate_number if obj.car else 'Не указано'}"
    if not update.message.photo and not update.message.video and not update.message.document:
        forwarded_message = await context.bot.send_message(
            chat_id=TG_GROUP_ID,
            text=text
        )
    else:
        if update.message.photo:
            forwarded_message = await context.bot.send_photo(TG_GROUP_ID, photo=update.message.photo[-1].file_id, caption=text)
        if update.message.video:
            forwarded_message = await context.bot.send_video(TG_GROUP_ID, video=update.message.video.file_id, caption=text)
        if update.message.document:
            forwarded_message = await context.bot.send_document(TG_GROUP_ID, document=update.message.document.file_id, caption=text)

    await Feedback.objects.acreate(
        user_id=obj,
        message_id=message_id,
        admin_message_id=forwarded_message.message_id,
        admin_chat_id=TG_GROUP_ID,
        text=text,
        video=update.message.video.file_id if update.message.video else None,
        photo=update.message.photo[-1].file_id if update.message.photo else None,
        file=update.message.document.file_id if update.message.document else None
    )

    await update.message.reply_text(
        await get_word('suggestions received', update)
    )
    await main_menu(update, context)
    return ConversationHandler.END


@sync_to_async
def get_feedback_user(feedback):
    return feedback.user_id


async def handle_feedback_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        admin_message_id = update.message.reply_to_message.message_id
        feedback = await Feedback.objects.aget(admin_message_id=admin_message_id)
        user = await get_feedback_user(feedback)
        photo = update.message.photo[-1].file_id if update.message.photo else None
        video = update.message.video.file_id if update.message.video else None
        document = update.message.document.file_id if update.message.document else None
        text = update.message.caption if update.message.photo or update.message.video or update.message.document else update.message.text
        if not text:
            text = ''
        response_text = await get_word("message from admin", chat_id=user.user_id) + f"\n {text}"
        await send_newsletter(context.bot, user.user_id, response_text, photo, video, document, reply_to_message_id=feedback.message_id)
