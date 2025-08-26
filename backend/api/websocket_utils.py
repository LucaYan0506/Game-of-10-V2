from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import logging

logger = logging.getLogger(__name__)

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

def send_game_update(game_id, payload, message_type="update"):
    """
    Send real-time update to WebSocket clients for a specific game.

    Args:
        game_id (str): The game room identifier
        payload (str): The message payload to send
        message_type (str): Type of message, defaults to "update"
    """
    channel_layer = get_channel_layer()

    if not channel_layer:
        logger.warning("Channel layer not configured. WebSocket updates disabled.")
        return

    try:
        async_to_sync(channel_layer.group_send)(
            game_id,
            {
                "type": message_type,
                "payload": payload,
            }
        )
        logger.debug(f"Sent WebSocket update to game {game_id}: {payload}")
    except Exception as e:
        logger.error(f"Failed to send WebSocket update: {e}")
