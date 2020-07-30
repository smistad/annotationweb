from channels.generic.websocket import AsyncWebsocketConsumer
import json


class ExportProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.name = self.scope["url_route"]["kwargs"]
        self.group_name = "export_progress_group"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, data):
        data_json = json.loads(data)
        message = data_json["message"]
        await self.channel_layer.group_send(self.group_name, {'type': 'message', 'message': message})

    async def value_update(self, event):
        value = event["value"]
        await self.send(text_data=json.dumps({'value': value}))
