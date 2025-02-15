# myapp/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Можем читать GET-параметры из self.scope, если нужно
        # Присоединяемся, например, к некой "группе":
        self.room_group_name = 'chat_room'

        # Присоединяемся к группе каналов
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()  # Принимаем WebSocket-соединение

    async def disconnect(self, close_code):
        # При закрытии соединения удаляем из группы
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Получаем сообщение от клиента
    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Шлём сообщение группе
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # Обработка события из группы
    async def chat_message(self, event):
        message = event['message']

        # Отправляем обратно клиенту
        await self.send(text_data=json.dumps({
            'message': message
        }))
