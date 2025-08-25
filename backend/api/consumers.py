from channels.generic.websocket import WebsocketConsumer
import json
from asgiref.sync import async_to_sync


class gameConsumer(WebsocketConsumer):
    def connect(self):
        from .utils import has_active_game, get_active_game

        user = self.scope["user"]
        if not user.is_authenticated:
            self.send(text_data=json.dumps({
                'type':'error',
                'payload':'User is not logged in'
            }))
            self.close()
            return 

        if has_active_game(user) == False:
            self.send(text_data=json.dumps({
                'type':'error',
                'payload':"User doesn't have active game"
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
        print(f"Disconnected with code: {close_code}")

    def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            payload = text_data_json['payload']
        except (json.JSONDecodeError, KeyError):
            self.send(text_data=json.dumps({
                'type': 'error',
                'payload': 'Invalid message format'
            }))
            return

        # print(payload)

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type':'update',
                'payload':payload
            }
        )

    def update(self, event):
        payload = event['payload']
        
        self.send(text_data=json.dumps({
            'type':'update_received',
            'payload':payload
        }))

    def send_message(self, event):
        """Handle sending custom messages to websocket clients"""
        message_type = event['message_type']
        payload = event['payload']

        self.send(text_data=json.dumps({
            'type': message_type,
            'payload': payload
        }))

    def send_message(self, event):
        """Handle sending custom messages to websocket clients"""
        message_type = event['message_type']
        payload = event['payload']

        self.send(text_data=json.dumps({
            'type': message_type,
            'payload': payload
        }))