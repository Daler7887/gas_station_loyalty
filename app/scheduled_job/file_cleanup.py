import os
import time
import logging
import datetime

logger = logging.getLogger(__name__)

def delete_old_files():
    folder = "files/car_images"
    days_old = 30
    #"""Удаление файлов старше заданного количества дней."""
    now = time.time()  # Текущее время в секундах с начала эпохи (Unix timestamp)
    cutoff_time = now - (days_old * 86400)  # Перевод количества дней в секунды (86400 секунд в дне)

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
