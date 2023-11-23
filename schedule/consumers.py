import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import CustomUser, ChatMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_id = text_data_json['sender_id']
        receiver_id = text_data_json['receiver_id']
        room_name = text_data_json['room_name']

        image_url = await self.image(sender_id)
        await self.save_message(sender_id, receiver_id, message, room_name)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'image': image_url,
                'sender_id': sender_id
            }
        )

    async def chat_message(self, event):
        message = event['message']
        image = event['image']
        sender_id = event['sender_id']

        await self.send(text_data=json.dumps({
            'message': message,
            'image': image,
            'sender_id': sender_id
        }))

    @database_sync_to_async
    def image(self, sender_id):
        user = CustomUser.objects.get(id=sender_id)
        return user.profile.image.url if user.profile.image else None


    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, message, room_name):
        sender = CustomUser.objects.get(id=sender_id)
        receiver = CustomUser.objects.get(id=receiver_id)
        ChatMessage.objects.create(
            sender=sender,
            receiver=receiver,
            message=message,
            room_name=room_name
        )
