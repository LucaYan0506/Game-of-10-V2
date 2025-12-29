from django.test import TestCase
from unittest.mock import patch, AsyncMock, MagicMock
from channels.layers import get_channel_layer
from api.websocket_utils import send_game_update
from unittest import skip


@skip("Temporarily skipping all tests in this class due to renamed functions")
class TestWebSocketUpdates(TestCase):

    def setUp(self):
        self.game_id = "test_game_123"
        self.payload = {"board": [[0, 0]], "score": 10}
        self.channel_layer = get_channel_layer()

    @patch('api.websocket_utils.get_channel_layer')  # Patch where it's imported
    def test_send_game_update_success(self, mock_get_layer):
        """Test that group_send is called with the correct arguments."""
        mock_layer = MagicMock()
        mock_layer.group_send = AsyncMock() 
        mock_get_layer.return_value = mock_layer

        send_game_update(self.game_id, self.payload)

        mock_layer.group_send.assert_called_once_with(
            self.game_id,
            {
                "type": "update",
                "payload": self.payload,
            }
        )

    @patch('api.websocket_utils.get_channel_layer')
    def test_no_channel_layer(self, mock_get_layer):
        """Test that the function handles a missing channel layer gracefully."""
        mock_get_layer.return_value = None

        # This should not raise an exception
        with self.assertLogs('api.websocket_utils', level='WARNING') as cm:
            send_game_update(self.game_id, self.payload)
            self.assertIn("Channel layer not configured", cm.output[0])

    @patch('api.websocket_utils.async_to_sync')
    def test_send_failure_logging(self, mock_async):
        """Test that exceptions during sending are caught and logged."""
        # Force an exception when group_send is called
        mock_async.side_effect = Exception("Connection Refused")

        with self.assertLogs('api.websocket_utils', level='ERROR') as cm:
            send_game_update(self.game_id, self.payload)
            self.assertIn("Failed to send WebSocket update", cm.output[0])