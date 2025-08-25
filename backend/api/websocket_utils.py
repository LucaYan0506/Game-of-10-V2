from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

def send_game_message(game_id: str, message_type: str, payload: dict):
    """
    Send a websocket message to all clients in a game room

    Args:
        game_id: The game room identifier
        message_type: Type of message ('update_received', 'end', etc.)
        payload: Message payload data
    """
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            game_id,
            {
                'type': 'send_message',
                'message_type': message_type,
                'payload': payload
            }
        )

def send_game_end_message(game_id: str, winner_username: str, loser_username: str):
    """Send game end message to all players in the game"""
    send_game_message(game_id, 'end', {'winner': winner_username, 'loser': loser_username})
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

def send_game_message(game_id: str, message_type: str, payload: dict):
    """
    Send a websocket message to all clients in a game room

    Args:
        game_id: The game room identifier
        message_type: Type of message ('update_received', 'end', etc.)
        payload: Message payload data
    """
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            game_id,
            {
                'type': 'send_message',
                'message_type': message_type,
                'payload': payload
            }
        )

def send_game_end_message(game_id: str, winner_username: str, loser_username: str):
    """Send game end message to all players in the game"""
    send_game_message(game_id, 'end', {'winner': winner_username, 'loser': loser_username})