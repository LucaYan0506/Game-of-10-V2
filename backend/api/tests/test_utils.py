import unittest
from unittest.mock import patch, MagicMock
from api.utils import (
    has_active_game, get_active_game, is_creator,
    get_opponent_username, get_my_cards, is_my_turn,
    get_enemy_score, get_my_score
)


class TestGameUtils(unittest.TestCase):

    def setUp(self):
        # Setup Mock User
        self.user = MagicMock()

        # Setup Mock Games
        self.active_game = MagicMock()
        self.active_game.status = "IN_PROGRESS"
        self.active_game.creator_cards = '["1", "2"]'
        self.active_game.opponent_cards = '["3"]'
        self.active_game.creator_turn = True
        self.active_game.creator_point = 100
        self.active_game.opponent_point = 50

        self.finished_game = MagicMock()
        self.finished_game.status = "FINISHED"

    def test_has_active_game_true(self):
        """Should return True if user has at least one non-finished game."""
        self.user.created_games.all.return_value = [self.finished_game, self.active_game]
        self.user.opponent_games.all.return_value = []

        self.assertTrue(has_active_game(self.user))

    def test_get_active_game(self):
        """Should return the first active game."""
        self.user.created_games.all.return_value = [self.active_game]
        self.user.opponent_games.all.return_value = []

        self.assertEqual(get_active_game(self.user), self.active_game)

    def test_get_active_game_raises_exception(self):
        """Should raise Exception if no active games exist."""
        self.user.created_games.all.return_value = [self.finished_game]
        self.user.opponent_games.all.return_value = []

        with self.assertRaises(Exception) as context:
            get_active_game(self.user)
        self.assertEqual(str(context.exception), "user dont have active game")

    def test_is_creator(self):
        """Verify logic that checks if game belongs to user's created_games."""
        self.user.created_games.all.return_value = [self.active_game]
        self.assertTrue(is_creator(self.user, self.active_game))

        self.user.created_games.all.return_value = []
        self.assertFalse(is_creator(self.user, self.active_game))

    def test_get_opponent_username_as_creator(self):
        """If user is creator, should return the opponent's name."""
        self.active_game.opponent.username = "EnemyPlayer"
        self.user.created_games.all.return_value = [self.active_game]

        name = get_opponent_username(self.user, self.active_game)
        self.assertEqual(name, "EnemyPlayer")

    def test_get_opponent_username_as_opponent(self):
        """If user is opponent, should return the creator's name."""
        self.active_game.creator.username = "CreatorPlayer"
        self.user.opponent_games.all.return_value = [self.active_game]

        name = get_opponent_username(self.user, self.active_game)
        self.assertEqual(name, "CreatorPlayer")

    @patch('api.utils.is_creator')
    def test_get_opponent_username_no_opponent_yet(self, mock_is_creator):
        """Case: I am the creator, but no one has joined the second slot yet."""
        mock_is_creator.return_value = True
        self.active_game.opponent = None  # Slot is empty

        result = get_opponent_username(self.user, self.active_game)
        self.assertEqual(result, "")

    @patch('api.utils.is_creator')
    def test_get_opponent_username_no_creator(self, mock_is_creator):
        """Case: I am the 'opponent', but the creator has deleted their account/left."""
        mock_is_creator.return_value = False
        self.active_game.creator = None  # Creator is missing

        result = get_opponent_username(self.user, self.active_game)
        self.assertEqual(result, "")

    def test_is_my_turn(self):
        """Test turn logic for both creator and opponent."""
        # Case: User is creator and it is creator's turn
        self.user.created_games.all.return_value = [self.active_game]
        self.active_game.creator_turn = True
        self.assertTrue(is_my_turn(self.user, self.active_game))

        # Case: User is opponent but it is creator's turn
        self.user.created_games.all.return_value = []  # Not creator
        self.assertTrue(not is_my_turn(self.user, self.active_game))

    def test_get_my_cards(self):
        """Verify creator gets creator_cards and opponent gets opponent_cards."""
        # Test as Creator
        self.user.created_games.all.return_value = [self.active_game]
        self.assertEqual(get_my_cards(self.user, self.active_game), '["1", "2"]')

        # Test as Opponent
        self.user.created_games.all.return_value = []
        self.assertEqual(get_my_cards(self.user, self.active_game), '["3"]')

    @patch('api.utils.is_creator')
    def test_get_my_score_as_creator(self, mock_is_creator):
        """As creator, my score should be creator_point."""
        mock_is_creator.return_value = True

        score = get_my_score(self.user, self.active_game)
        self.assertEqual(score, 100)

    @patch('api.utils.is_creator')
    def test_get_enemy_score_as_creator(self, mock_is_creator):
        """As creator, enemy score should be opponent_point."""
        mock_is_creator.return_value = True

        score = get_enemy_score(self.user, self.active_game)
        self.assertEqual(score, 50)

    # --- Perspective: USER IS OPPONENT ---

    @patch('api.utils.is_creator')
    def test_get_my_score_as_opponent(self, mock_is_creator):
        """As opponent, my score should be opponent_point."""
        mock_is_creator.return_value = False

        score = get_my_score(self.user, self.active_game)
        self.assertEqual(score, 50)

    @patch('api.utils.is_creator')
    def test_get_enemy_score_as_opponent(self, mock_is_creator):
        """As opponent, enemy score should be creator_point."""
        mock_is_creator.return_value = False

        score = get_enemy_score(self.user, self.active_game)
        self.assertEqual(score, 100)
