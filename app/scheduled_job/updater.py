from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events, DjangoJobStore
from app.scheduled_job import *
from app.scheduled_job.file_cleanup import delete_old_files
from app.refuiling import *
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.StreamHandler()])

logger = logging.getLogger(__name__)

class jobs:
    scheduler = BackgroundScheduler(timezone='Asia/Tashkent')
    scheduler.add_jobstore(DjangoJobStore(), 'djangojobstore')
    
    #logger.info("Добавление задачи 'process_fuel_sales_log' с интервалом 5 секунд.")
    #scheduler.add_job(process_fuel_sales_log, 'interval', seconds=10, max_instances=1)
    
    logger.info("Добавление задачи на удаление файлов каждое 1-е число месяца.")
    scheduler.add_job(delete_old_files, 'cron', day=1, hour=0, minute=0, max_instances=1)

    register_events(scheduler)
    # logger.info("Планировщик запущен.")