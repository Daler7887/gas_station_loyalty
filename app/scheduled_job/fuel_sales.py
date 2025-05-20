from datetime import datetime, timedelta
from app.models import FuelSale, Organization, Pump, PlateRecognition
from django.db import transaction
from bot.utils.bot_functions import *
from config import TG_GROUP_ID
from bot.utils import bot
from app.utils.smb_utils import read_file
import requests
import logging
import os

logger = logging.getLogger(__name__)


def process_fuel_sales_log():
    organizations = Organization.objects.select_related('server').all()
    for org in organizations:
        smb_server = org.server
        if not smb_server:
            logger.info(f"У организации {org} не указан SMB-сервер")
            continue

        last_processed_timestamp = org.last_processed_timestamp if org.last_processed_timestamp else datetime.now() - \
            timedelta(days=1)
        current_date = datetime.now().date()
        last_date = last_processed_timestamp.date()

        file_path = last_processed_timestamp.strftime("%Y%m%d")
        smb_file_path = os.path.join(
            smb_server.share_name, last_processed_timestamp.strftime("%Y"), file_path + ".txt")

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

                event_type = line[21:23]
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

                # get the latest plate recognition
                last_record = PlateRecognition.objects.filter(
                    recognized_at__lte=timestamp, recognized_at__gte=timestamp - timedelta(minutes=5), pump=pump).order_by('-recognized_at').first()

                # Сохраняем данные в базе данных
                new_log = FuelSale(
                    date=timestamp,
                    organization=org,
                    quantity=quantity,
                    price=price,
                    total_amount=total_amount,
                    pump=pump,
                    plate_recognition=last_record
                )
                new_logs.append(new_log)

                if last_record is not None:
                    pass
                    # send_sales_info_to_tg(new_log)

        except FileNotFoundError as e:
            logger.error(f"Ошибка при чтении {file_path}: {e}")

        if new_logs:
            with transaction.atomic():
                FuelSale.objects.bulk_create(new_logs)
                org.last_processed_timestamp = new_logs[-1].datetime
                org.save(update_fields=["last_processed_timestamp"])

        # if last_date < current_date - timedelta(days=2):
        #     org.last_processed_timestamp = last_date + timedelta(days=1)
        #     org.save()


def send_sales_info_to_tg(new_log):
    photo_path = new_log.plate_recognition.image2

    message_text = fr'''
      <b>⛽ Продажа топлива</b>

📅 Дата: {new_log.date.strftime('%d.%m.%Y')}
⏰ Время: {new_log.date.strftime('%H:%M:%S')}
🏢 Организация: {new_log.organization}

🚗 Номер машины: <b>{new_log.plate_recognition.number}</b>
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
