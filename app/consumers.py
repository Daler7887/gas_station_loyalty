# myapp/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from app.models import Pump, OrganizationAccess
from app.utils.queries import aget_pump_info
from urllib.parse import parse_qs


class PumpConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        query = parse_qs(self.scope["query_string"].decode())
        org_id = query.get("org_id", [None])[0]

        if user is None or not user.is_authenticated or org_id is None:
            await self.close()
            return

        org_id = int(org_id)

        # Проверяем доступ
        if not await self.has_organization_access(user, org_id):
            await self.close()
            return
        
        self.org_id = org_id
        self.room_group_name = f"pumps_org_{org_id}"
        await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
        await self.accept()
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
        pump_list = await aget_pump_info(org_id=self.org_id)
        await self.send(text_data=json.dumps({
            'pumps': pump_list
        }))

    @database_sync_to_async
    def has_organization_access(self, user, org_id):
        if user.is_superuser:
            return True
        return OrganizationAccess.objects.filter(user=user, organization_id=org_id).exists()