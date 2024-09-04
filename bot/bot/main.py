from bot.bot import *

        
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(update.message.chat_id, 'Hello')
