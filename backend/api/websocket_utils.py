from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


# Send to the frontend a message saying that there is new update
def send_web_socket_message(game_id: str, payload: dict, message_type: str):
    channel_layer = get_channel_layer()

    if not channel_layer:
        logger.warning("Channel layer not configured. WebSocket updates disabled.")
        return

    try:
        async_to_sync(channel_layer.group_send)(
            game_id,
            {
                "type": message_type,
                "message_type": message_type,
                "game_id": game_id,
                "payload": payload,
            }
        )
        logger.debug(f"Sent WebSocket update to game {game_id}: {payload}")
    except Exception as e:
        logger.error(f"Failed to send WebSocket update: {e}")
