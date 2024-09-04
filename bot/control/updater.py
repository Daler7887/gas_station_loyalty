import asyncio
from dataclasses import dataclass
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ExtBot,
    TypeHandler,
)
from telegram import Update
from config import BOT_API_TOKEN, WEBHOOK_URL
from bot.control.handlers import handlers


@dataclass
class WebhookUpdate:
    """Simple dataclass to wrap a custom update type"""
    user_id: int
    payload: str

class CustomContext(CallbackContext[ExtBot, dict, dict, dict]):
    @classmethod
    def from_update(
        cls,
        update: object,
        application: "Application",
    ) -> "CustomContext":
        if isinstance(update, WebhookUpdate):
            return cls(application=application, user_id=update.user_id)
        return super().from_update(update, application)

context_types = ContextTypes(context=CustomContext)
application = Application.builder().token(BOT_API_TOKEN).context_types(context_types).build()

# add handlers
for handler in handlers[::-1]:
    application.add_handler(handler)


### webhook functions
async def set_webhook():
    await application.bot.set_webhook(
            url=f"{WEBHOOK_URL}/{BOT_API_TOKEN}", 
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
            )

async def delete_webhook():
    await application.bot.delete_webhook()