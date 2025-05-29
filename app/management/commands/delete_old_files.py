from django.core.management.base import BaseCommand
from app.scheduled_job.jobs import delete_old_files

class Command(BaseCommand):
    help = 'Delete old files from the specified folder.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to delete old files...')
        try:
            delete_old_files()
            self.stdout.write(self.style.SUCCESS('Successfully deleted old files.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error occurred: {e}'))
