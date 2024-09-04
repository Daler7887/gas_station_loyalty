from django.core.management.base import BaseCommand
from bot.control.updater import application
import asyncio

class Command(BaseCommand):
    help = 'Command to polling bot'

    def handle(self, *args, **options):
        asyncio.run(
            application.run_polling()
        )