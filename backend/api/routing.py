from django.urls import re_path
from api.consumers import GameConsumer

websocket_urlpatterns = [
    re_path(r'ws/socket-server/', GameConsumer.as_asgi()),
]
