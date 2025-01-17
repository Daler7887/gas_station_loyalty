import requests
import logging
from config import ALPR_TOKEN

# Настройка логирования
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

def read_plate(uploaded_file):
    """
    Анализирует изображение номера автомобиля из InMemoryUploadedFile.

    Args:
        uploaded_file (InMemoryUploadedFile): Загруженный файл, который нужно обработать.

    Returns:
        str: Номерной знак (plate) или None, если распознавание не удалось.
    """
    try:
        #logger.info("Sending image to Plate Recognizer API...")
        response = requests.post(
            'https://api.platerecognizer.com/v1/plate-reader/',
            files={'upload': uploaded_file},
            headers={'Authorization': f'Token {ALPR_TOKEN}'}
        )
        if response.ok:
            json_data = response.json()
            results = json_data.get('results', [])
            if results and 'plate' in results[0]:
                plate = results[0]['plate']
                return plate
            else:
                #logger.warning("No plate found in the API response.")
                return 'error'
        else:
            #`logger.error(f"API request failed with status {response.status_code}: {response.text}")
            return 'error'
    except requests.exceptions.RequestException as e:
        #logger.error(f"An error occurred while making the API request: {e}")
        return "error"
