from smb.SMBConnection import SMBConnection
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

def read_file(server_ip, share_name, file_path, username="", password=""):
    """Открывает соединение, читает файл и сразу закрывает соединение"""
    try:
        # Создаём новое соединение
        conn = SMBConnection(
            username=username or '',
            password=password or '',
            my_name="DjangoApp",
            remote_name=server_ip,
            use_ntlm_v2=True,
            is_direct_tcp=True
        )
        conn.connect(server_ip, 445)

        # Читаем файл
        file_obj = BytesIO()
        conn.retrieveFile(share_name, file_path, file_obj)

        file_obj.seek(0)
        conn.close()
        return file_obj

    except Exception as e:
        logger.error(f"Ошибка при чтении файла {file_path}: {e}")
        return None
