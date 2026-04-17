import json
from channels.generic.websocket import AsyncWebsocketConsumer


class TruckCycleConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer para actualizaciones en tiempo real del Ciclo del Camión.
    Solo envía signals de "algo cambió" — el frontend hace refetch por HTTP.
    """

    async def connect(self):
        self.dc_id = self.scope['url_route']['kwargs']['dc_id']
        self.group_name = f'truck_cycle_cd_{self.dc_id}'

        user = self.scope.get('user')
        if not user or user.is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def pauta_updated(self, event):
        """Envía signal de actualización al cliente"""
        await self.send(text_data=json.dumps({
            'type': 'pauta_updated',
            'pauta_id': event.get('pauta_id'),
            'status': event.get('status'),
            'transport_number': event.get('transport_number'),
        }))
