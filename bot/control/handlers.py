from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    InlineQueryHandler,
    TypeHandler,
    ConversationHandler
)

from bot.bot import (
    main,
    login,
    suggestions
)
from bot.resources.conversationList import *
from bot.resources.strings import lang_dict

login_handler = ConversationHandler(
    entry_points=[CommandHandler("start", main.start)],
    states={
        GET_LANG: [
            MessageHandler(filters.Text(lang_dict["uz_ru"]), login.get_lang),
            MessageHandler(filters.TEXT & (~filters.COMMAND), login.get_lang)
        ],
        GET_NAME: [
            MessageHandler(filters.TEXT & (~filters.COMMAND), login.get_name)
        ],
        GET_CONTACT: [
            MessageHandler(filters.CONTACT, login.get_contact),
            MessageHandler(filters.Text(lang_dict['back']), login.get_contact),
            MessageHandler(filters.TEXT & (
                ~filters.COMMAND), login.get_contact)
        ],
        GET_PLATE_NUMBER: [
            MessageHandler(filters.TEXT & (~filters.COMMAND),
                           login.get_plate_number)
        ]
    },
    fallbacks=[
        CommandHandler("start", login.start)
    ],
    name="login",
)

settings_handler = MessageHandler(filters.Text(
    lang_dict['settings']), main.settings_menu)
# change_name_handler = MessageHandler(filters.Text(lang_dict['change name']), main.change_name)
# change_phone_handler = MessageHandler(filters.Text(lang_dict['change phone number']), main.change_phone)
main_menu_handler = MessageHandler(
    filters.Text(lang_dict['main menu']), main.main_menu)

balance_handler = MessageHandler(filters.Text(
    lang_dict['balance']), main.get_balance)

change_lang_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Text(
        lang_dict['change lang']), main.change_lang)],
    states={
        CHANGE_LANG: [
            MessageHandler(filters.TEXT & (~filters.COMMAND), main.set_lang)
        ],
    },
    fallbacks=[
        MessageHandler(filters.Text(lang_dict['main menu']), main.main_menu),
        CommandHandler("start", main.start)
    ],
    name="change_lang"
)
change_name_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Text(
        (lang_dict['change name'])), main.change_name)],
    states={
        CHANGE_NAME: [
            MessageHandler(filters.TEXT & (~filters.COMMAND), main.set_name)
        ],

    },
    fallbacks=[
        MessageHandler(filters.Text(lang_dict['main menu']), main.main_menu),
        CommandHandler("start", main.start)
    ],
    name="change_name"
)
change_phone_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Text(
        lang_dict['change phone number']), main.change_phone)],
    states={
        CHANGE_PHONE: [
            MessageHandler(filters.CONTACT, main.set_phone),
            MessageHandler(filters.TEXT & (~filters.COMMAND), main.set_phone)
        ],
    },
    fallbacks=[
        MessageHandler(filters.Text(lang_dict['back']), main.settings_menu),
        CommandHandler("start", main.start)
    ],
    name="change_phone"
)

change_plate_number_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Text(
        lang_dict['change plate number']), main.change_plate_number)],
    states={
        CHANGE_PLATE_NUMBER: [
            MessageHandler(filters.TEXT & (~filters.COMMAND),
                           main.set_plate_number)
        ],
    },
    fallbacks=[
        MessageHandler(filters.Text(lang_dict['back']), main.settings_menu),
        CommandHandler("start", main.start)
    ],
    name="change_plate_number"
)

suggestions_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Text(
        lang_dict['feedback']), suggestions.handle_suggestions)],
    states={
        GET_SUGGESTION: [
            MessageHandler(filters.ALL & ~filters.COMMAND, suggestions.receive_suggestions),
        ]
    },
    fallbacks=[
        MessageHandler(filters.Text(lang_dict['back']), main.start),
        CommandHandler("cancel", main.start),  
        CommandHandler("start", main.start)
    ],
    name="handle_suggestions"
)

feedback_handler_answer = MessageHandler(filters.ALL & filters.ChatType.GROUPS & ~filters.COMMAND, suggestions.handle_feedback_response)

fallback_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, main.handle_fallback)

handlers = [
    CallbackQueryHandler(
        main.handle_callback_query, pattern=r"^bonus_"),
    fallback_handler,
    login_handler,
    settings_handler,  # Добавляем обработчик для меню настроек
    change_lang_handler,  # Добавляем обработчик для смены языка
    change_name_handler,  # Добавляем обработчик для смены имени
    change_phone_handler,  # Добавляем обработчик для смены номера телефона
    main_menu_handler,  # Добавляем обработчик для возврата в главное меню
    suggestions_handler,
    feedback_handler_answer,
    balance_handler,
    change_plate_number_handler
]
