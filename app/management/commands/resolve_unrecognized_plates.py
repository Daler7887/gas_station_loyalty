from django.core.management.base import BaseCommand
from app.scheduled_job.unrecognized_plates import resolve_unrecognized_plates

class Command(BaseCommand):
    help = 'Resolve unrecognized plates for FuelSale records.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to resolve unrecognized plates...')

        resolve_unrecognized_plates()

        self.stdout.write(self.style.SUCCESS('Successfully resolved unrecognized plates.'))
