from django.core.management.base import BaseCommand
from bot.control.updater import set_webhook
import asyncio

class Command(BaseCommand):
    help = 'Command that set webhook'

    def handle(self, *args, **options):
        asyncio.run(
            set_webhook()
        )