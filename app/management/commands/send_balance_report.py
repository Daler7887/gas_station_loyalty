from django.core.management.base import BaseCommand
from app.scheduled_job.balance_report import send_balance_report

class Command(BaseCommand):
    help = "Генерирует и отправляет отчет по бонусам в Telegram"

    def handle(self, *args, **kwargs):
        send_balance_report()
