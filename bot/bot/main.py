from bot.bot import *
from asgiref.sync import sync_to_async, async_to_sync
from app.models import Car, PlateRecognition
from bot.utils.clients import validate_plate_number
from telegram.ext import CallbackContext
from config import TG_GROUP_ID

FEEDBACK_CHANNEL_ID = -1002144060952


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if await is_group(update):
        return

    if await is_registered(update.message.chat.id):
        await main_menu(update, context)
        return ConversationHandler.END
    else:
        hello_text = lang_dict['hello']
        await update_message_reply_text(
            update,
            hello_text,
            reply_markup=await select_lang_keyboard()
        )
        return GET_LANG


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update = update.callback_query if update.callback_query else update

    bot = context.bot
    keyboards = [
        [await get_word('change lang', update), await get_word('change name', update)],
        [await get_word('change phone number', update), await get_word('change plate number', update)],
        [await get_word('main menu', update)]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard=keyboards, resize_keyboard=True)
    await bot.send_message(
        update.message.chat_id,
        await get_word('settings', update),
        reply_markup=reply_markup
    )


async def get_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    try:
        user = await Bot_user.objects.aget(user_id=user_id)
        car = await sync_to_async(lambda: user.car)()
        if car:
            balance = car.loyalty_points
        else:
            balance = 0
        msg = await get_word('user balance', update)
        await update.message.reply_text(msg.format(balance), parse_mode=ParseMode.MARKDOWN_V2)
    except Bot_user.DoesNotExist:
        await update.message.reply_text('User does not exist.')
    await main_menu(update, context)


async def get_common_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = await common_questions_keyboard(update)
    message = await get_word('common questions', update)
    await update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(
        keyboard=keyboard, resize_keyboard=True, one_time_keyboard=False
    ))
    return COMMON_QUESTIONS


async def select_common_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question_text = update.message.text
    user = await Bot_user.objects.aget(user_id=update.message.chat.id)
    try:
        question = await CommonQuestions.objects.aget(
            question_uz=question_text) if user.lang == 'uz' else await CommonQuestions.objects.aget(
            question_ru=question_text)
        answer = question.answer_uz if user.lang == 'uz' else question.answer_ru
        await update.message.reply_text(answer)
    except CommonQuestions.DoesNotExist:
        await update.message.reply_text(await get_word('question not found', update))
    
    return COMMON_QUESTIONS


async def get_gas_stations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = await stations_keyboard(update)
    await update.message.reply_text(
        await get_word('our stations', update),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=keyboard, resize_keyboard=True, one_time_keyboard=False
        )
    )
    return SELECT_STATION


async def select_station(update: Update, context: ContextTypes.DEFAULT_TYPE):
    station_name = update.message.text
    user = await Bot_user.objects.aget(user_id=update.message.chat.id)
    try:
        station = await Organization.objects.aget(adress=station_name) if user.lang == 'ru' else await Organization.objects.aget(adress_uz=station_name)
        await update.message.reply_location(latitude=str(station.latitude), longitude=str(station.longitude))

        if station.redeem_start_time and station.redeem_end_time:
            message = (await get_word('station bonus time', update)).format(
                station.redeem_start_time.strftime("%H:%M"),
                station.redeem_end_time.strftime("%H:%M")
            )
            await update.message.reply_text(message)
        
    except Organization.DoesNotExist:
        await update.message.reply_text(await get_word('station not found', update))
    return SELECT_STATION


async def change_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update_message_reply_text(
        update,
        "Bot tilini tanlang\n\nВыберите язык бота",
        reply_markup=await select_lang_keyboard()
    )
    return CHANGE_LANG


async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "UZ" in text:
        lang = 'uz'
    elif "RU" in text:
        lang = 'ru'
    else:
        return await change_lang(update, context)
    try:
        await get_or_create(user_id=update.message.chat_id)
        obj = await get_object_by_user_id(user_id=update.message.chat_id)
        obj.lang = lang
        await obj.asave()
        await settings_menu(update, context)
    except Bot_user.DoesNotExist:
        await update.message.reply_text('User does not exist.')
    return ConversationHandler.END


async def change_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await get_word('send new name', update)
    keyboard = ReplyKeyboardMarkup([[await get_word('back', update)]], resize_keyboard=True)
    await update.message.reply_text(message, reply_markup=keyboard)
    return CHANGE_NAME


async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_message_back(update):
        await settings_menu(update, context)
        return ConversationHandler.END
    user_id = update.message.chat.id
    name = update.message.text
    try:
        user = await sync_to_async(Bot_user.objects.get)(user_id=user_id)
        user.name = name
        await sync_to_async(user.save)()
        message = await get_word('changed your name', update)
        await update.message.reply_text(message)
    except Bot_user.DoesNotExist:
        await update.message.reply_text('User does not exist.')
    await settings_menu(update, context)
    return ConversationHandler.END


async def change_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact_button = KeyboardButton(text=await get_word('leave number', update), request_contact=True)
    keyboard = ReplyKeyboardMarkup([[contact_button], [await get_word('back', update)]], resize_keyboard=True)
    message = await get_word('send new phone number', update)
    await update.message.reply_text(message, reply_markup=keyboard)
    return CHANGE_PHONE


async def change_plate_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await get_word('send new plate number', update)
    keyboard = ReplyKeyboardMarkup([[await get_word('back', update)]], resize_keyboard=True)
    await update.message.reply_text(message, reply_markup=keyboard)
    return CHANGE_PLATE_NUMBER


async def set_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_message_back(update):
        await settings_menu(update, context)
        return ConversationHandler.END
    user_id = update.message.chat.id
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    try:
        user = await sync_to_async(Bot_user.objects.get)(user_id=user_id)
        user.phone = phone
        await sync_to_async(user.save)()
        message = await get_word('changed your phone number', update)
        await update.message.reply_text(message)
    except Bot_user.DoesNotExist:
        await update.message.reply_text('User does not exist.')
    await settings_menu(update, context)
    return ConversationHandler.END


async def set_plate_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_message_back(update):
        await settings_menu(update, context)
        return ConversationHandler.END
    user_id = update.message.chat.id
    plate_number = update.message.text.upper()
    if not await validate_plate_number(plate_number):
        await update.message.reply_text('Неверный формат номера автомобиля')
        return CHANGE_PLATE_NUMBER
    try:
        user = await sync_to_async(Bot_user.objects.get)(user_id=user_id)
        car = await sync_to_async(Car.objects.get_or_create)(plate_number=plate_number)
        user.car = car[0]
        await sync_to_async(user.save)()
        message = await get_word('changed your plate number', update)
        await update.message.reply_text(message)
    except Bot_user.DoesNotExist:
        await update.message.reply_text('User does not exist.')
    await settings_menu(update, context)
    return ConversationHandler.END


async def handle_callback_query(update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data.startswith('bonus_'):
        record_id = data.split('_')[1]
        updated = await PlateRecognition.objects.filter(
            id=record_id,
            is_processed=False,
            use_bonus=False,
        ).aupdate(use_bonus=True)

        await query.edit_message_reply_markup(reply_markup=None)
        if updated == 0:
            await query.answer(await get_word('bonus not allowed', query))
        else:
            await query.answer(await get_word('success', query))
            await query.message.edit_text(query.message.text + "\n\n" + await get_word("use bonus", query) + " ✅")
        

async def handle_fallback(update, context):
    message = update.message
    is_reply_to_admin = False
    if message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id:
        admin_msg = ''
        if update.message.reply_to_message.text:
            admin_msg = update.message.reply_to_message.text
        if update.message.reply_to_message.caption:
            admin_msg = update.message.reply_to_message.caption
        is_reply_to_admin = admin_msg.startswith("📢 **Ответ от Команды Поддержки** 📢")

    if is_reply_to_admin:    
        try:
            text = ''
            if update.message.text:
                text = update.message.text
            if update.message.caption:
                text = update.message.caption
            message_id = update.message.message_id
            obj = await get_object_by_user_id(user_id=update.message.chat.id)

            text = f"{text}\n\nОтзыв от @{update.message.from_user.username}:\nНомер телефона: {obj.phone}\nНомер автомобиля: {obj.car.plate_number if obj.car else 'Не указано'}"
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
                await get_word('thanks for answer, wait for response', update)
            )
            await main_menu(update, context)
            return ConversationHandler.END
        except:
            await message.reply_text(await get_word("something went wrong, try again later", update))
    else:
        await message.reply_text(await get_word("something went wrong, send /start and try again", update))