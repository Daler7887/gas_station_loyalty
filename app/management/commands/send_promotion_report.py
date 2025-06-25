from django.core.management.base import BaseCommand
from app.scheduled_job.promotion_report import send_promotion_report

class Command(BaseCommand):
    help = "Генерирует и отправляет отчет по продвижению в Telegram"

    def handle(self, *args, **kwargs):
        send_promotion_report()
