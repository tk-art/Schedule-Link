import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import CustomUser, ChatMessage
from .views import human_readable_time_from_utc

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["user"].id
        self.user_group_name = f'user_{self.user_id}'

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_id = text_data_json['sender_id']
        receiver_id = text_data_json['receiver_id']
        room_name = text_data_json['room_name']
        temporary_id = text_data_json['temporaryId']

        image_url = await self.image(sender_id)
        save_message = await self.save_message(sender_id, receiver_id, message, room_name)
        message_id = save_message.id
        chat = await self.delta(sender_id, message)

        await self.channel_layer.group_send(
            f'user_{sender_id}',
            {
                'type': 'sender_chat_message',
                'message_id': message_id,
                'temporary_id': temporary_id
            }
        )

        await self.channel_layer.group_send(
            f'user_{receiver_id}',
            {
                'type': 'chat_message',
                'message': message,
                'image': image_url,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'chat': chat,
                'message_id': message_id
            }
        )

    async def sender_chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message_id': event['message_id'],
            'temporary_id': event['temporary_id']
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'image': event['image'],
            'sender_id': event['sender_id'],
            'receiver_id': event['receiver_id'],
            'chat': event['chat'],
            'message_id': event['message_id']
        }))

    async def send_read_receipt(self, event):
        await self.send(text_data=json.dumps({
            'action': 'readReceipt',
            'message_id': event['message_id']
        }))

    @database_sync_to_async
    def image(self, sender_id):
        user = CustomUser.objects.get(id=sender_id)
        return user.profile.image.url if user.profile.image else None

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, message, room_name):
        sender = CustomUser.objects.get(id=sender_id)
        receiver = CustomUser.objects.get(id=receiver_id)

        return ChatMessage.objects.create(
            sender=sender,
            receiver=receiver,
            message=message,
            room_name=room_name
        )

    @database_sync_to_async
    def delta(self, sender_id, message):
        chat = ChatMessage.objects.filter(sender=sender_id, message=message).first()
        chat.delta = human_readable_time_from_utc(chat.timestamp)
        return chat.delta
