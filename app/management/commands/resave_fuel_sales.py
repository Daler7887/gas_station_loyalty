from django.core.management.base import BaseCommand
from app.models import FuelSale
from datetime import datetime

class Command(BaseCommand):
    help = 'Resave all FuelSale records to trigger any save logic or updates.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specify the date (YYYY-MM-DD) to filter FuelSale records. Defaults to all records.',
        )

    def handle(self, *args, **kwargs):
        date_str = kwargs.get('date')
        if date_str:
            try:
                filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                self.stdout.write(f'Filtering FuelSale records for date: {filter_date}')
                fuel_sales = FuelSale.objects.filter(date__date=filter_date)
            except ValueError:
                self.stderr.write('Invalid date format. Please use YYYY-MM-DD.')
                return
        else:
            self.stdout.write('No date provided. Resaving all FuelSale records...')
            return

        total = fuel_sales.count()
        for index, sale in enumerate(fuel_sales, start=1):
            sale.save()
            self.stdout.write(f'Resaved {index}/{total} FuelSale records', ending='\r')

        self.stdout.write(self.style.SUCCESS('Successfully resaved all FuelSale records.'))
