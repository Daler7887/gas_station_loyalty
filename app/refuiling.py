from datetime import datetime, timedelta
from .models import FuelSale, LogProcessingMetadata, Organization, Pump, PlateRecognition
from bot.utils.bot_functions import *
from config import TG_GROUP_ID
from bot.utils import bot
import requests
import logging

logger = logging.getLogger(__name__)

def process_fuel_sales_log():
    #  pass
    # Получаем последний обработанный лог
    Organizations = Organization.objects.all()
    for Orgs in Organizations:

        last_metadata = LogProcessingMetadata.objects.filter(
            organization=Orgs).first()
        last_processed_timestamp = last_metadata.last_processed_timestamp if last_metadata else None

        file_path = datetime.now().strftime("%Y%m%d")
        new_logs = []

        try:
            with open(Orgs.log_path + datetime.now().strftime("%Y") + "/" + file_path + ".txt", 'r') as file:

                for line in file:

                    event_type = line[26:28]
                    try:
                        timestamp = datetime.strptime(
                            line[:21], "%y-%m-%d %H:%M:%S:%f")
                    except:
                        continue
                    # Пропускаем уже обработанные строки
                    if event_type != "TR" or (last_processed_timestamp and timestamp <= last_processed_timestamp):
                        continue

                    pump_number, price, quantity, total_amount = parse_log_line(
                        line)
                    if quantity == 0 and total_amount == 0:
                        continue

                    pump = Pump.objects.filter(
                        number=pump_number, organization=Orgs).first()
                    if not pump:
                        pump = Pump.objects.create(
                            number=pump_number, organization=Orgs, ip_address="")

                    # get the latest plate recognition
                    last_record = PlateRecognition.objects.filter(
                        recognized_at__lte=timestamp, recognized_at__gte=timestamp - timedelta(minutes=5), pump=pump).order_by('-recognized_at').first()

                    # Сохраняем данные в базе данных
                    new_log = FuelSale(
                        date=timestamp,
                        organization=Orgs,
                        quantity=quantity,
                        price=price,
                        total_amount=total_amount,
                        pump=pump,
                        plate_recognition=last_record
                    )
                    new_logs.append(new_log)

                    if last_record != None:
                        send_sales_info_to_tg(new_log)

        except FileNotFoundError as e:
            logger.error(f"Ошибка при чтении {file_path}: {e}")   

        if new_logs:
            FuelSale.objects.bulk_create(new_logs)
            # Обновляем метаданные
            if not last_metadata:
                last_metadata = LogProcessingMetadata()
            last_metadata.last_processed_timestamp = new_logs[-1].date
            last_metadata.organization = Orgs
            last_metadata.save()


def send_sales_info_to_tg(new_log):
    photo_path = new_log.plate_recognition.image2 

    message_text = fr'''
      <b>⛽ Продажа топлива</b>

📅 Дата: {new_log.date.strftime('%d.%m.%Y')}
⏰ Время: {new_log.date.strftime('%H:%M:%S')}
🏢 Организация: {new_log.organization}

🚗 Номер машины: <b>{new_log.plate_recognition.number}</b>
🛢️ Колонка: {new_log.pump.number}

⛽ Количество топлива: {new_log.quantity} литров
💵 Цена за литр: {new_log.price} сум
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
