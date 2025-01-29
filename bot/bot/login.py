from bot.bot import *
from bot.utils.clients import validate_plate_number
from app.models import Car


async def _to_the_select_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update_message_reply_text(
        update,
        "Bot tilini tanlang\n\nВыберите язык бота",
        reply_markup=await select_lang_keyboard()
    )
    return GET_LANG


async def _to_the_getting_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update_message_reply_text(
        update,
        await get_word("type name", update),
        reply_markup=await reply_keyboard_markup([[await get_word("back", update)]])
    )
    return GET_NAME


async def _to_the_getting_contact(update: Update):
    i_contact = KeyboardButton(
        text=await get_word("leave number", update),
        request_contact=True
    )

    await update_message_reply_text(
        update,
        await get_word("send number", update),
        reply_markup=await reply_keyboard_markup(
            [[i_contact], [await get_word("back", update)]],
        )
    )

    return GET_CONTACT


async def _to_the_getting_plate_number(update: Update):
    await update_message_reply_text(
        update,
        await get_word("leave plate number", update),
        reply_markup=await reply_keyboard_markup([[await get_word("back", update)]])
    )

    return GET_PLATE_NUMBER


###################################################################################
###################################################################################

async def get_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "UZ" in text:
        lang = 'uz'
    elif "RU" in text:
        lang = 'ru'
    else:
        return await _to_the_select_lang(update, context)

    await get_or_create(user_id=update.message.chat_id)
    obj = await get_object_by_user_id(user_id=update.message.chat_id)
    obj.lang = lang
    await obj.asave()

    return await _to_the_getting_name(update, context)


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_message_back(update):
        return await _to_the_select_lang(update, context)

    obj = await get_object_by_update(update)
    obj.name = update.message.text
    obj.username = update.message.chat.username
    obj.firstname = update.message.chat.first_name
    await obj.asave()

    return await _to_the_getting_contact(update)


async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_message_back(update):
        return await _to_the_getting_name(update, context)

    # check message type is contact, else return
    if update.message.contact == None or not update.message.contact:
        await update.message.reply_text(await get_word("click button leave number", update), parse_mode=ParseMode.MARKDOWN)
        return GET_CONTACT

    # get phone number from message
    phone_number = update.message.contact.phone_number
    # check phone number is registred in the past or not
    is_available = await filter_objects_sync(Bot_user, {'phone': phone_number})
    if is_available:
        await update.message.reply_text(
            await get_word("number is logged", update)
        )
        return GET_CONTACT

    obj = await get_object_by_update(update)
    obj.phone = phone_number
    await obj.asave()
    return await _to_the_getting_plate_number(update)


async def get_plate_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_message_back(update):
        return await _to_the_getting_contact(update)

    if not await validate_plate_number(update.message.text):
        await update.message.reply_text(await get_word("incorrect plate number", update))
        return GET_PLATE_NUMBER
    obj = await get_object_by_update(update)
    car = await sync_to_async(Car.objects.get_or_create)(plate_number=update.message.text)
    obj.car = car[0]
    await obj.asave()
    await main_menu(update, context)
    return ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _to_the_select_lang(update, context)
