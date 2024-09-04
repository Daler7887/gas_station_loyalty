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
)

start = CommandHandler('start', main.start)

handlers = [
    start
]