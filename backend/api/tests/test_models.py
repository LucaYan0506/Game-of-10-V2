from django.test import TestCase
from api.models import Game
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from unittest.mock import MagicMock
from api.game_models.game_state import GameState
from api.game_models.card import Card
import json


class TestGame(TestCase):
    def test_get_value_from_label(self):
        standard_game_type = Game.get_value_from_label('Standard', Game.GameType)
        self.assertEqual(standard_game_type, "STANDARD")
        single_card_game_type = Game.get_value_from_label('Single Card', Game.GameType)
        self.assertEqual(single_card_game_type, "SINGLE_CARD")
        hard_game_type = Game.get_value_from_label('Hard', Game.GameType)
        self.assertEqual(hard_game_type, "HARD")

        pvp_game_mode = Game.get_value_from_label('PvP', Game.GameMode)
        self.assertEqual(pvp_game_mode, "PvP")
        pvai_game_mode = Game.get_value_from_label('PvAi', Game.GameMode)
        self.assertEqual(pvai_game_mode, "PvAi")

        invalid_game_type_label = ['', 'ads', None, 123, 'PvP', 'PvAi']
        for label in invalid_game_type_label:
            invalid_game_type = Game.get_value_from_label(label, Game.GameType)
            self.assertIsNone(invalid_game_type)
        invalid_game_mode_label = ['', 'ads', None, 123, 'Standard', 'Game of x', 'Hard']
        for label in invalid_game_mode_label:
            invalid_game_type = Game.get_value_from_label(label, Game.GameMode)
            self.assertIsNone(invalid_game_type)

    def test_pvp_with_ai_model_fails(self):
        """PvP games should not have an AI model assigned."""
        game = Game(game_mode=Game.GameMode.PVP, ai_model="SomeModel")
        with self.assertRaises(ValidationError):
            game.full_clean()

    def test_pvai_with_human_opponent_fails(self):
        """PvAI games should not have a human opponent."""
        opponent = User.objects.create_user("test", "", "passwd")
        game = Game(game_mode=Game.GameMode.PVAI, opponent=opponent)
        with self.assertRaises(ValidationError):
            game.full_clean()

    def test_pvai_invalid_ai_model_choices(self):
        """PvAI games must have a valid AI model from choices."""
        invalid_models = [None, "invalid_choice", "", "123"]
        for model in invalid_models:
            game = Game(game_mode=Game.GameMode.PVAI, ai_model=model)
            with self.assertRaises(ValidationError):
                game.full_clean()

    def test_auto_delete_if_no_players(self):
        """Game should delete itself if both creator and opponent are None."""
        game = Game.objects.create(
            game_id='1',  # random id
            game_mode=Game.GameMode.PVP,
            creator=None,
            opponent=None
        )
        game.save()
        # Check if the object still exists in the DB
        exists = Game.objects.filter(game_id=game.game_id).exists()
        self.assertFalse(exists, "The game instance should have been deleted.")

    def test_str_representation(self):
        """Test the __str__ method output."""
        game = Game(game_id=101, game_mode=Game.GameMode.PVP)
        self.assertEqual(str(game), "Game 101 (PvP)")


class TestGameState(TestCase):

    def setUp(self):
        """Set up a mock Game object to avoid database overhead."""
        self.mock_game = MagicMock(spec=Game)
        # use fake board and pool
        self.mock_game.board = json.dumps([["A", "B"], ["C", "D"]])
        self.mock_game.pool = "ABCDEFGHIJKLMNOP"
        self.mock_game.creator_cards = json.dumps(["1", "2", "*"])
        self.mock_game.opponent_cards = json.dumps(["5", "7", "/"])
        self.mock_game.creator_point = 10
        self.mock_game.opponent_point = 5
        self.mock_game.creator_turn = True

    def test_initialization_parsing(self):
        """Test that JSON strings from Game are correctly parsed into lists."""
        state = GameState(self.mock_game)

        # Test list parsing
        self.assertEqual(state.board, [["A", "B"], ["C", "D"]])
        self.assertEqual(state.creator_cards, ["1", "2", "*"])
        self.assertEqual(state.opponent_cards, ["5", "7", "/"])

        # Test basic field mapping
        self.assertEqual(state.pool, "ABCDEFGHIJKLMNOP")
        self.assertEqual(state.creator_point, 10)
        self.assertTrue(state.creator_turn)

    def test_default_values(self):
        """Test that winner and tie have the correct starting values."""
        state = GameState(self.mock_game)
        self.assertEqual(state.winner, '')
        self.assertFalse(state.tie)

    def test_json_decode_error(self):
        """Test how GameState handles corrupted/invalid JSON in the database."""
        self.mock_game.board = "invalid-json-string"

        with self.assertRaises(json.JSONDecodeError):
            GameState(self.mock_game)


class TestCard(TestCase):

    def test_card_initialization(self):
        """Test that attributes are assigned correctly."""
        card = Card(i=2, j=3, val="+", id=101)
        self.assertEqual(card.i, 2)
        self.assertEqual(card.j, 3)
        self.assertEqual(card.val, "+")
        self.assertEqual(card.id, 101)

    def test_str_and_repr(self):
        """Test that the string output is formatted as expected."""
        card = Card(1, 1, "5", 1)
        expected_output = "\n      5 at i=1 j=1"
        self.assertEqual(str(card), expected_output)
        self.assertEqual(repr(card), expected_output)

    def test_equality(self):
        """Cards with same i, j, and val should be equal (ignoring id)."""
        card1 = Card(0, 0, "A", 1)
        card2 = Card(0, 0, "A", 2)  # Different ID
        card3 = Card(0, 1, "A", 1)  # Different position

        self.assertEqual(card1, card2)
        self.assertNotEqual(card1, card3)
        self.assertNotEqual(card1, "Not a Card object")

    def test_hashability(self):
        """Test that Card can be used in a set and behaves consistently."""
        card1 = Card(0, 0, "X", 1)
        card2 = Card(0, 0, "X", 2)

        # Because __eq__ and __hash__ match, these should be seen as the same in a set
        card_set = {card1, card2}
        self.assertEqual(len(card_set), 1)

    def test_hash_consistency(self):
        """Hash should be the same for identical i, j, val."""
        card1 = Card(5, 5, "9", 1)
        card2 = Card(5, 5, "9", 500)
        self.assertEqual(hash(card1), hash(card2))
