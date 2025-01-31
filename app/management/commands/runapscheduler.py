from django.core.management.base import BaseCommand
from apscheduler.schedulers.background import BackgroundScheduler
from app.scheduled_job.jobs import process_fuel_sales_log

class Command(BaseCommand):
    help = 'Run APScheduler'

    def handle(self, *args, **options):
        scheduler = BackgroundScheduler()
        scheduler.add_job(process_fuel_sales_log, 'interval', seconds=5)
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
