
import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.layers import get_channel_layer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django_asgi_app = get_asgi_application()

from apps.user.socket.routing import websocket_urlpatterns
from apps.truck_cycle.socket.routing import websocket_urlpatterns as truck_cycle_ws
from apps.tv.socket.routing import websocket_urlpatterns as tv_ws
from middleware.jwt_middleware import JwtAuthMiddlewareStack
from django.conf import settings

# JwtAuthMiddleware deja pasar (AnonymousUser) cuando no hay ?token en la query,
# así que el WS de TV funciona sin auth — el `code` en la URL ya es la llave.
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JwtAuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns + truck_cycle_ws + tv_ws
        )
    ),
})

# obtener el estado del canal
channel_layer = get_channel_layer()