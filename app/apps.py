from django.apps import AppConfig
import os


class app(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        import app.signals
        run_once = os.environ.get('CMDLINERUNNER_RUN_ONCE')
        if run_once is not None:
            print('Scheduler already started')
            return
        print('Starting scheduler...')
        os.environ['CMDLINERUNNER_RUN_ONCE'] = 'True'
        # from app.scheduled_job.updater import jobs
        # jobs.scheduler.start()
        from app.scheduled_job.jobs import start_scheduler
        start_scheduler()
