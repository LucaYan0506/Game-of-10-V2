from django.urls import path
from api.consumers import GameConsumer

websocket_urlpatterns = [
    path('ws/socket-server/', GameConsumer.as_asgi()),
]
