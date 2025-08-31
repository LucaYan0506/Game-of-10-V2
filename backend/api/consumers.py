from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from api.models import Game
import json
import logging

logger = logging.getLogger(__name__)


class GameConsumer(WebsocketConsumer):
    def connect(self):
        from .utils import has_active_game, get_active_game

        user = self.scope["user"]
        if not user.is_authenticated:
            self.send(text_data=json.dumps({
                'message_type': 'error',
                'payload': 'User is not logged in'
            }))
            self.close()
            return

        if not has_active_game(user):
            self.send(text_data=json.dumps({
                'message_type': 'error',
                'payload': "User doesn't have active game"
            }))
            self.close()
            return

        self.room_group_name = get_active_game(user).game_id

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        logger.debug(f"Disconnected with code: {close_code}")

    def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            payload = text_data_json['payload']
        except (json.JSONDecodeError, KeyError):
            self.send(text_data=json.dumps({
                'message_type': 'error',
                'payload': 'Invalid message format'
            }))
            return

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'update',
                'message_type': 'update',
                'payload': payload,
            }
        )

    def update(self, event):
        payload = event['payload']
        message_type = event.get('message_type', 'update_received')

        self.send(text_data=json.dumps({
            'message_type': message_type,
            'payload': payload
        }))

    def game_end(self, event):
        game = Game.objects.get(game_id=event['game_id'])
        board = json.loads(game.board)
        creator_point = game.creator_point
        opponent_point = game.opponent_point
        creator = game.creator
        payload = event['payload'].copy()
        payload['board'] = board

        # prepare message differently for each player
        if self.scope["user"] == creator:
            payload['myScore'] = creator_point
            payload['enemyScore'] = opponent_point
        else:
            payload['myScore'] = opponent_point
            payload['enemyScore'] = creator_point

        self.send(text_data=json.dumps({
            'message_type': 'game_end',
            'payload': payload
        }))
