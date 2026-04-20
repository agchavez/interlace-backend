from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/tv/(?P<code>[A-Z0-9\-]{3,16})/$', consumers.TvPairingConsumer.as_asgi()),
]
