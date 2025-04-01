from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # id de la sala solo enteros
        re_path(r'ws/notification/(?P<room_name>\d+)/$', consumers.NotificationConsumer.as_asgi()),
]