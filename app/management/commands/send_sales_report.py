from django.core.management.base import BaseCommand
from app.scheduled_job.sales_report import send_sales_report

class Command(BaseCommand):
    help = "Генерирует и отправляет отчет по продажам в Telegram"

    def handle(self, *args, **kwargs):
        send_sales_report()
