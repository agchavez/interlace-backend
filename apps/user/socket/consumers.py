import json
from json import JSONDecodeError

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.user.models.notificacion import NotificationModel
from apps.user.serializers.notificacion import NotificationSerializer


@database_sync_to_async
def get_notification_data(user_id):
    return NotificationSerializer(
        NotificationModel.objects.filter(user=user_id, read=False),
        many=True
    ).data

class NotificationConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room = None
        self.user = None

    async def connect(self):
        self.room = self.scope['url_route']['kwargs']['room_name']
        self.user = self.scope['user']
        # The room id must match the user's id
        if self.room != str(self.user.id):
            await self.close()

        await self.channel_layer.group_add(
            self.room,
            self.channel_name
        )
        await self.accept()

        data = await get_notification_data(self.user.id)
        await self.send(text_data=json.dumps({
            'type': 'data_notification',
            'data': data
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            message = json.loads(text_data)
            if('type' not in message):
                await self.send(text_data=json.dumps({
                    'error': 'Invalid message type'
                }))
                return

            message_type = message['type']

            if message_type == 'chat_message':
                await self.channel_layer.group_send(
                    self.room,
                    {
                        'type': 'chat_message',
                        'message': message['message']
                    }
                )
            elif message_type == 'data_notification':
                data = await get_notification_data(self.user.id)
                await self.send(text_data=json.dumps({
                    'type': 'data_notification',
                    'data': data
                }))
            else:
                await self.send(text_data=json.dumps({
                    'error': 'Invalid message type'
                }))
        except JSONDecodeError:
            await self.send(text_data=json.dumps({'error': 'Invalid JSON message.'}))
            return
        except ValueError as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))

    async def chat_message(self, event):
        message = event['message']
        # Send the message to the WebSocket client
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))

    async def data_notification(self, event):
        data = event['data']
        await self.send(text_data=json.dumps({
            'type': 'data_notification',
            'data': data
        }))

    async def send_notification(self, event):
        data = event['data']
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'data': data
        }))

    # Mark as read
    async def notification_read(self, event):
        data = event['data']
        await self.send(text_data=json.dumps({
            'type': 'notification_read',
            'data': data
        }))

    # All notifications read
    async def notifications_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'z'
        }))
