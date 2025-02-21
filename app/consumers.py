# myapp/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from app.models import Pump
from app.utils.queries import aget_pump_info

class PumpConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope['user'] is None or not self.scope['user'].is_authenticated:
            await self.close()
        else:
            self.room_name = 'pumps'
            self.room_group_name = 'pumps_group'

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()

            # Send initial pump information
            await self.send_pump_info()

    async def disconnect(self, close_code):
        # Leave room group only if it was set during connect
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if message == 'get_pump_info':
            await self.send_pump_info()
       

    async def pump_message(self, event):
        message = event['pumps']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'pumps': message
        }))


    async def send_pump_info(self):
        pump_list = await aget_pump_info()
        await self.send(text_data=json.dumps({
            'pumps': pump_list
        }))