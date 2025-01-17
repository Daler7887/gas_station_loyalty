from telegram import Update
from telegram.ext import ConversationHandler
from bot.services.language_service import get_word
from bot.bot import *

FEEDBACK_CHANNEL_ID = "-4628250515"


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
    user_id = update.message.chat.id
    text = update.message.text
    message_id = update.message.message_id
    suggestion = update.message.text
    forwarded_message = await context.bot.send_message(
        chat_id=FEEDBACK_CHANNEL_ID,
        text=f"Отзыв от \b{update.message.from_user.username}: \n {suggestion}"
    )
    await Feedback.objects.acreate(
        user_id=user_id,
        message_id=message_id,
        admin_message_id=forwarded_message.message_id,
        admin_chat_id=FEEDBACK_CHANNEL_ID,
        category="Отзыв",
        text=text
    )
    context.user_data['suggestion_message_id'] = forwarded_message.message_id
    await update.message.reply_text(
        await get_word('suggestions received', update)
    )
    await main_menu(update, context)
    return ConversationHandler.END


async def handle_feedback_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != int(FEEDBACK_CHANNEL_ID):
        return
    if update.message.reply_to_message:
        admin_message_id = update.message.reply_to_message.message_id
        feedback = await Feedback.objects.aget(admin_message_id=admin_message_id)

        response_text = update.message.text

        await context.bot.send_message(
            chat_id=feedback.user_id,
            text= await get_word("message from admin", chat_id=feedback.user_id) + f"\n {response_text}",
            reply_to_message_id=feedback.message_id
        )