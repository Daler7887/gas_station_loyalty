from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from .smb_utils import SMBReader
from app.models import Organization

# Глобальная переменная, чтобы держать соединение
smb_reader = None


def init_smb_connection():
    """Инициализация SMBReader при старте планировщика."""
    global smb_reader
    if smb_reader is None:
        smb_reader = SMBReader(
            server_ip='10.253.10.150',
            share_name='wooriposlog',
            client_machine_name='MY_CLIENT',
            server_name='10.253.10.150',
            username="",      # Анонимный доступ, если разрешён
            password="",
            port=445,
            use_ntlm_v2=True,
            is_direct_tcp=True
        )


def read_file_task():
    """Задача, которая вызывается каждые 5 секунд."""
    global smb_reader
    try:
        # Предположим, что внутри wooriposlog есть папка "2025" и файл "somefile.txt"
        file_path = "2025/20250128.txt"
        file_contents = smb_reader.retrieve_file(file_path)
        print('Файл прочитан')
    except Exception as e:
        print("Ошибка при чтении файла:", e)


def start_scheduler():
    init_smb_connection()

    scheduler = BackgroundScheduler()
    # Запуск read_file_task каждые 5 секунд
    print('добавил задачу')
    scheduler.add_job(read_file_task, 'interval', minutes=10)
    scheduler.start()
