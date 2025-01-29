from smb.SMBConnection import SMBConnection
from io import BytesIO

server_ip = '10.253.10.150'
share_name = 'wooriposlog'
file_path = '2025\\20250128.txt'

client_machine_name = 'MY_CLIENT'
server_name = '10.253.10.150'  # Можно указать IP, если неизвестно NetBIOS-имя

try:
    conn = SMBConnection(
        username="",  # Пустой логин (анонимный)
        password="",  # Пустой пароль
        my_name=client_machine_name,
        remote_name=server_name,
        use_ntlm_v2=True,
        is_direct_tcp=True  # Включаем прямое TCP-соединение (SMB2/SMB3)
    )
    # Пробуем порт 445 (SMB Direct TCP)
    connected = conn.connect(server_ip, 445)

    if connected:
        print("Успешно подключились!")
        file_obj = BytesIO()
        file_attributes, file_size = conn.retrieveFile(
            share_name, file_path, file_obj)
        file_obj.seek(0)
        print(file_obj.read().decode('utf-8', errors='replace'))
    else:
        print("Не удалось подключиться.")
except Exception as e:
    print(f"Ошибка: {e}")
finally:
    if 'conn' in locals():
        conn.close()
