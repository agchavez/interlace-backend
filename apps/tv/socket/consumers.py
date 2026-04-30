"""
Consumer del WebSocket de pareo de TVs.

Flujo:
1. La TV abre WS a /ws/tv/<code>/ ni bien muestra el QR.
2. El consumer valida que el code exista y esté en PENDING, y se une al grupo
   `tv_session_<code>`.
3. Cuando el usuario confirma pareo (HTTP), la view dispara `group_send` con el
   evento `session.paired` que contiene el access_token + config.
4. La TV recibe el evento, guarda el token y navega al dashboard.

También maneja eventos de `session.updated` (cambio de dashboard sin reparear)
y `session.revoked` (token cancelado desde admin) para que la TV reaccione.
"""
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from ..models import TvSession


class TvPairingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.code = self.scope['url_route']['kwargs']['code']
        self.group_name = f'tv_session_{self.code}'

        session = await self._get_session(self.code)
        if not session:
            # Code desconocido — cerramos con código custom para que el cliente
            # sepa que es error lógico, no de red.
            await self.close(code=4404)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Si ya está pareada (reconexión), avisar al cliente inmediatamente.
        if session.status == 'PAIRED' and not session.is_expired:
            await self.send(text_data=json.dumps({
                'type': 'session.paired',
                'access_token': session.access_token,
                'dashboard': session.dashboard,
                'distributor_center': session.distributor_center_id,
                'distributor_center_name': session.distributor_center.name if session.distributor_center else None,
                'expires_at': session.expires_at.isoformat(),
                'config': session.config,
                'label': session.label,
            }))
        elif session.status == 'PENDING':
            await self.send(text_data=json.dumps({
                'type': 'session.pending',
                'expires_at': session.expires_at.isoformat(),
            }))
        else:
            # Revocada o expirada — cliente debe reiniciar el flujo.
            await self.send(text_data=json.dumps({
                'type': 'session.invalid',
                'status': session.status,
            }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # ---- Handlers disparados por group_send desde la view ----
    async def session_paired(self, event):
        await self.send(text_data=json.dumps({'type': 'session.paired', **event['data']}))

    async def session_updated(self, event):
        await self.send(text_data=json.dumps({'type': 'session.updated', **event['data']}))

    async def session_revoked(self, event):
        await self.send(text_data=json.dumps({'type': 'session.revoked'}))

    async def workstation_config_updated(self, event):
        """Disparado cuando un admin edita el workstation config del CD pareado."""
        await self.send(text_data=json.dumps({
            'type': 'workstation.config.updated',
            **event.get('data', {}),
        }))

    @database_sync_to_async
    def _get_session(self, code):
        try:
            return TvSession.objects.select_related('distributor_center').get(code=code)
        except TvSession.DoesNotExist:
            return None
