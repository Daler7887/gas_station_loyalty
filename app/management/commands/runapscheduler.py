from django.core.management.base import BaseCommand
from apscheduler.schedulers.background import BackgroundScheduler
from app.scheduled_job.jobs import process_fuel_sales_log, delete_old_files
from app.scheduled_job.balance_report import send_balance_report
from app.scheduled_job.sales_report import send_sales_report
from app.scheduled_job.unrecognized_plates import resolve_unrecognized_plates

class Command(BaseCommand):
    help = 'Run APScheduler'

    def handle(self, *args, **options):
        scheduler = BackgroundScheduler()
        scheduler.add_job(process_fuel_sales_log, 'interval', seconds=5)
        scheduler.add_job(delete_old_files, 'cron', hour=3, minute=0)
        scheduler.add_job(send_balance_report, 'cron', hour=0, minute=0)
        scheduler.add_job(send_sales_report, 'cron', hour=0, minute=0)
        scheduler.add_job(resolve_unrecognized_plates, 'interval', hours=2)
        scheduler.start()

        self.stdout.write(self.style.SUCCESS('Scheduler started!'))

        # Ждём сигнала (Ctrl+C или kill)
        import time
        try:
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
            self.stdout.write(self.style.SUCCESS('Scheduler stopped!'))
