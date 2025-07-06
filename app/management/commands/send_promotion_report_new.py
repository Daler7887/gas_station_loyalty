from django.core.management.base import BaseCommand
from app.scheduled_job.promotion_report_new import send_promotion_report_new
import asyncio


class Command(BaseCommand):
    help = "Генерирует и отправляет отчет по продвижению в Telegram"

    def handle(self, *args, **kwargs):
        asyncio.run(send_promotion_report_new())
