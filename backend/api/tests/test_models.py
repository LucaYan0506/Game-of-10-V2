from django.test import TestCase
from api.models import Game


class TestGame(TestCase):
    def test_get_value_from_label(self):
        standard_game_type = Game.get_value_from_label('Standard', Game.GameType)
        self.assertEqual(standard_game_type, "STANDARD")
        game_of_x_game_type = Game.get_value_from_label('Game of x', Game.GameType)
        self.assertEqual(game_of_x_game_type, "GAME_OF_X")
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
