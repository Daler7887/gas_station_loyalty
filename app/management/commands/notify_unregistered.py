from django.core.management.base import BaseCommand
from app.models import FuelSale
from datetime import datetime
import asyncio
from bot.models import Bot_user
from bot.utils.bot_functions import send_newsletter, bot
from bot.services.language_service import get_word

async def notify_unregistered_users():
    unregistered_users = Bot_user.objects.filter(
        car__isnull=True,
    )
    async for user in unregistered_users:
        # Here you would implement the logic to notify the user
        # For example, sending a message via a bot or email
        print(f"Notifying user: {user.phone}")
        await send_newsletter(bot, user.user_id, await get_word("please register", chat_id = user.user_id))
        

class Command(BaseCommand):
    help = 'Notify about unregistered fuel sales'

    def handle(self, *args, **options):
        # Get all unregistered fuel sales
        asyncio.run(notify_unregistered_users())