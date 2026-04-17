from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/truck-cycle/(?P<dc_id>\d+)/$', consumers.TruckCycleConsumer.as_asgi()),
]
