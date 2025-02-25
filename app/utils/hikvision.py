from email.parser import BytesParser
from email.policy import default
from django.core.files.base import ContentFile
from app.models import PlateRecognition, Pump
import requests
from requests.auth import HTTPDigestAuth
import xmltodict
import logging

logger = logging.getLogger(__name__)


def start_manual_anpr(pump):
    # URL для отправки запроса
    url = f"http://{pump.public_ip}:{pump.public_port}/ISAPI/Traffic/MNPR/channels/1"
    # Учетные данные для Digest авторизации
    username = pump.login
    password = pump.password

    try:
        # Выполняем GET-запрос (verify=False НЕБЕЗОПАСНО и годится лишь для теста)
        response = requests.get(
            url,
            auth=HTTPDigestAuth(username, password),
            verify=False
        )

        # Проверка статуса ответа
        if response.status_code != 200:
            logger.error(
                f"Request failed with status code: {response.status_code}")
            return

        content_type = response.headers.get("Content-Type", "")
        if "multipart" not in content_type or "boundary=" not in content_type:
            # Предположим, что boundary='boundary'
            content_type = "multipart/form-data; boundary=boundary"

        mime_header = (
            f"Content-Type: {content_type}\r\n"
            "MIME-Version: 1.0\r\n"
            "\r\n"
        )

        # Объединяем наш «поддельный» заголовок с контентом ответа
        raw_data = mime_header.encode("utf-8") + response.content

        # Парсим как полноценное MIME-сообщение
        msg = BytesParser(policy=default).parsebytes(raw_data)

        # Хранилища для XML и изображений
        xml_data = None
        images = {}

        # 5) Идём по всем частям сообщения
        for part in msg.walk():
            # Content-Type каждой части
            ctype = part.get_content_type()
            # filename может быть взято из заголовка Content-Disposition
            filename = part.get_filename()

            # Если это XML
            if ctype == "text/xml":
                xml_data = part.get_payload(decode=True)  # байты XML
            # Если это потенциально картинка, либо явно указан filename
            elif ctype.startswith("image/") or filename:
                if not filename:
                    # Если имя не обнаружено, дадим что-нибудь
                    filename = "unknown_image.jpg"
                # Извлекаем байты изображения
                image_bytes = part.get_payload(decode=True)
                images[filename] = image_bytes

        # Проверяем, что XML нашёлся
        if not xml_data:
            ("XML data not found in the response")
            return

        # Парсим XML
        xml_text = xml_data.decode("utf-8", errors="replace")
        parsed_data = xmltodict.parse(xml_text)

        # Далее всё зависит от структуры XML:
        event = parsed_data.get("EventNotificationAlert", {})
        anpr_data = event.get("ANPR", {})

        picture_info_list = anpr_data.get(
            "pictureInfoList", {}).get("pictureInfo")
        if not picture_info_list:
            logger.error("No pictureInfo found in XML")
            return

        # Может быть словарь (одно изображение) или список (несколько)
        if isinstance(picture_info_list, dict):
            picture_info_list = [picture_info_list]

        # Извлекаем файлы (байты) по именам
        image1_bytes = None
        image2_bytes = None

        if len(picture_info_list) >= 1:
            fname1 = picture_info_list[0].get("fileName")
            image1_bytes = images.get(fname1)
        if len(picture_info_list) >= 2:
            fname2 = picture_info_list[1].get("fileName")
            image2_bytes = images.get(fname2)

        # Извлекаем IP-адрес и дату
        ip_address = event.get("ipAddress")
        date_time = event.get("dateTime")

        if not ip_address or not date_time:
            logger.error("No ipAddress or dateTime in XML")
            return

        recognized_at = date_time[:19] if len(date_time) >= 19 else date_time

        pump = Pump.objects.filter(ip_address=ip_address).first()
        if not pump:
            logger.error(f"Pump with ip_address={ip_address} not found")
            return

        plate_number = anpr_data.get("licensePlate")
        # Создаём новую запись
        new_record = PlateRecognition(
            pump=pump,
            number=plate_number,
            recognized_at=recognized_at
        )
        if image1_bytes:
            new_record.image1.save("vehiclePicture.jpg",
                                   ContentFile(image1_bytes), save=False)
        if image2_bytes:
            new_record.image2.save(
                "detectionPicture.jpg", ContentFile(image2_bytes), save=False)
        new_record.save()
        return new_record
    except Exception as e:
        logger.info(f"Error during manual ANPR: {e}")
        return None


def get_parking_plate_number(pump):
    if pump.public_ip is None or pump.public_port is None:
        return None
    url = f"http://{pump.public_ip}:{pump.public_port}/ISAPI/Parking/channels/1/parkingStatus"
    username = pump.login
    password = pump.password

    try:
        response = requests.get(
            url,
            auth=HTTPDigestAuth(username, password),
            verify=False
        )

        if response.status_code != 200:
            logger.error(
                f"Request failed with status code: {response.status_code}")
            return None

        # Parse XML response
        xml_text = response.content.decode("utf-8", errors="replace")
        parsed_data = xmltodict.parse(xml_text)

        # Extract plateNo
        parking_status_list = parsed_data.get("ParkingStatusCap", {}).get(
            "ParkingStatusList", {}).get("ParkingStatus", {})
        plate_no = parking_status_list.get("plateNo", None)
        return plate_no

    except Exception as e:
        logger.info(f"Error during get parking status: {e}")
        return None
