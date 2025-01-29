from smb.SMBConnection import SMBConnection
from io import BytesIO

class SMBReader:
    def __init__(
        self,
        server_ip: str,
        share_name: str,
        client_machine_name: str,
        server_name: str,
        username: str = "",
        password: str = "",
        port: int = 445,
        use_ntlm_v2: bool = True,
        is_direct_tcp: bool = True
    ):
        self.server_ip = server_ip
        self.share_name = share_name
        self.client_machine_name = client_machine_name
        self.server_name = server_name
        self.username = username
        self.password = password
        self.port = port
        self.use_ntlm_v2 = use_ntlm_v2
        self.is_direct_tcp = is_direct_tcp

        self.conn = None
        self._connect()

    def _connect(self):
        """Инициализация соединения."""
        self.conn = SMBConnection(
            self.username,
            self.password,
            self.client_machine_name,
            self.server_name,
            use_ntlm_v2=self.use_ntlm_v2,
            is_direct_tcp=self.is_direct_tcp
        )
        self.conn.connect(self.server_ip, self.port)

    def retrieve_file(self, file_path: str) -> str:
        """Читает содержимое файла по заданному пути."""
        if not self.conn:
            self._connect()

        file_obj = BytesIO()
        self.conn.retrieveFile(self.share_name, file_path, file_obj)
        file_obj.seek(0)
        return file_obj.read().decode('utf-8', errors='replace')

    def close(self):
        """Закрывает соединение."""
        if self.conn:
            self.conn.close()
            self.conn = None
