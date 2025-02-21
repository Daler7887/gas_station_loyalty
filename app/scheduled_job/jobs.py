from datetime import datetime, timedelta
from app.models import FuelSale, Organization, Pump, PlateRecognition, Car
from django.db import transaction
from bot.utils.bot_functions import *
from config import TG_GROUP_ID
from bot.utils import bot
from app.utils.smb_utils import read_file
from app.utils.hikvision import get_parking_plate_number
from apscheduler.schedulers.background import BackgroundScheduler
from app.utils.queries import PLATE_NUMBER_TEMPLATE as plate_templates
import requests
import logging
import os
import time
import re

logger = logging.getLogger(__name__)


def delete_old_files():
    folder = "files/car_images"
    days_old = 30
    # """Удаление файлов старше заданного количества дней."""
    now = time.time()  # Текущее время в секундах с начала эпохи (Unix timestamp)
    # Перевод количества дней в секунды (86400 секунд в дне)
    cutoff_time = now - (days_old * 86400)

    # Проходим по файлам в папке
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)

        try:
            if os.path.isfile(file_path):
                # Получаем время создания файла
                file_creation_time = os.path.getctime(file_path)

                # Если файл старше cutoff_time, удаляем его
                if file_creation_time < cutoff_time:
                    os.remove(file_path)
                    logger.info(f"Файл {file_path} успешно удалён.")

        except Exception as e:
            logger.error(f"Ошибка при удалении {file_path}: {e}")


def process_fuel_sales_log():
    logger.info('started processing')
    organizations = Organization.objects.select_related('server').all()
    for org in organizations:
        smb_server = org.server
        if not smb_server or not smb_server.active:
            logger.info(f"У организации {org} не указан SMB-сервер")
            continue

        last_processed_timestamp = org.last_processed_timestamp if org.last_processed_timestamp else datetime.now() - \
            timedelta(days=31)
        current_date = datetime.now().date()
        last_date = last_processed_timestamp.date()
        file_path = last_processed_timestamp.strftime("%Y%m%d")
        smb_file_path = os.path.join(
            last_processed_timestamp.strftime("%Y"), file_path + ".txt")

        new_logs = []
        try:
            file_obj = read_file(
                smb_server.server_ip, smb_server.share_name, smb_file_path, smb_server.username, smb_server.password)

            if not file_obj:
                continue

            for line in file_obj:
                line = line.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                event_type = line[26:28]
                try:
                    timestamp = datetime.strptime(
                        line[:21], "%y-%m-%d %H:%M:%S:%f")
                except:
                    continue

                # Пропускаем уже обработанные строки
                if event_type != "TR" or (timestamp <= last_processed_timestamp):
                    continue
                pump_number, price, quantity, total_amount = parse_log_line(
                    line)
                if quantity == 0 and total_amount == 0:
                    continue

                pump, _ = Pump.objects.get_or_create(number=pump_number, organization=org, defaults={
                                                     "number": pump_number, "ip_address": "", "organization": org})

                plate_recog = PlateRecognition.objects.filter(pump=pump, recognized_at__gte=timestamp-timedelta(minutes=15), is_processed=False, number__regex=plate_templates).order_by('-recognized_at').first()
                if plate_recog is None:
                    plate_recog = PlateRecognition.objects.filter(pump=pump, recognized_at__gte=timestamp-timedelta(minutes=15), is_processed=False).order_by('-recognized_at').first()
                plate_number = plate_recog.number if plate_recog else None
                # get the latest plate recognition
                new_client = not Car.objects.filter(
                    plate_number=plate_number).exists() if plate_number is not None and re.match(plate_templates, plate_number) else False
                # Сохраняем данные в базе данных
                new_log = FuelSale(
                    date=timestamp,
                    organization=org,
                    quantity=quantity,
                    price=price,
                    total_amount=total_amount,
                    final_amount=total_amount,
                    pump=pump,
                    plate_number=plate_number,
                    plate_recognition=plate_recog,
                    new_client=new_client
                )
                new_logs.append(new_log)
                with transaction.atomic():
                    new_log.save()
                    if plate_recog:
                        plate_recog.is_processed = True
                        plate_recog.save()
                    org.last_processed_timestamp = timestamp
                    org.save()

                if plate_number is not None and re.match(plate_templates, plate_number):
                    pass
                    # send_sales_info_to_tg(new_log)

        except FileNotFoundError as e:
            logger.info(f'Ошибка при чтении файла: {e}')

        if last_date < current_date:
            org.last_processed_timestamp = last_date + timedelta(days=1)
            org.save()


def send_sales_info_to_tg(new_log):
    photo_path = new_log.plate_recognition.image2

    message_text = fr'''
      <b>⛽ Продажа топлива</b>

📅 Дата: {new_log.date.strftime('%d.%m.%Y')}
⏰ Время: {new_log.date.strftime('%H:%M:%S')}
🏢 Организация: {new_log.organization}

🚗 Номер машины: <b>{new_log.plate_number}</b>
🛢️ Колонка: {new_log.pump.number}

⛽ Количество топлива: {new_log.quantity} м/3
💵 Цена за м/3: {new_log.price} сум
💰 Общая сумма: <b>{new_log.total_amount}</b> сум '''

    url = f"https://api.telegram.org/bot{bot.token}/sendPhoto"
    payload = {'chat_id': TG_GROUP_ID,
               'caption': message_text, 'parse_mode': 'HTML'}

    response = requests.post(url, data=payload, files={'photo': photo_path})

    # response = requests.post(url, data=payload)


def parse_log_line(line):

    # номер колонки
    pump_id = int(line[23:25])
    # ЦенаЗаКуб = Число(Сред(Элемент, 29,6));
    price = int(line[28:34])
    # КоличествоКубов = Число(Сред(Элемент, 35,4)+"." + Сред(Элемент, 39,3));
    quantity = float(line[34:38] + "." + line[38:41])

    # СуммаКубов = Число(Сред(Элемент, 42,8));
    total_amount = int(line[41:49])

    return pump_id, price, quantity, total_amount


def start_scheduler():
    scheduler = BackgroundScheduler()
    # Запускаем каждые 5 секунд
    scheduler.add_job(process_fuel_sales_log, 'interval', seconds=5)
    scheduler.add_job(delete_old_files, 'cron', day=1, hour=0, minute=0)
    scheduler.start()
