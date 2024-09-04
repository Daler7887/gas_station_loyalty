from django.core.management.base import BaseCommand
from bot.control.updater import delete_webhook
import asyncio

class Command(BaseCommand):
    help = 'Command that delete webhook'

    def handle(self, *args, **options):
        asyncio.run(
            delete_webhook()
        )