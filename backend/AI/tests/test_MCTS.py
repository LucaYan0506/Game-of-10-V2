from django.test import TestCase
from AI.MCTS import Node
from unittest.mock import MagicMock
from api.models import Game
from api.game_models.game_state import GameState
from api.game_models.action import Action, ActionType
import json


class TestMCTS(TestCase):
    def test_is_fully_expanded(self):
        node = Node(None, MagicMock())
        node.potential_action = []
        node.tried_action = set()
        action = Action(ActionType.DISCARD, card_index=1)

        # len(potential_action) = 0, len(tried_action) = 0
        self.assertTrue(node.is_fully_expanded())

        # len(potential_action) = 1, len(tried_action) = 0
        node.potential_action.append(action)
        self.assertFalse(node.is_fully_expanded())

        # len(potential_action) = 1, len(tried_action) = 1
        node.tried_action.add(action)
        self.assertTrue(node.is_fully_expanded())

    def test_no_place_action(self):
        node = Node(None, MagicMock())
        node.potential_action = []
        node.tried_action = set()

        self.assertTrue(node.no_place_action())

        node.potential_action.append(Action(ActionType.DISCARD, card_index=1))
        self.assertTrue(node.no_place_action())

        node.potential_action.append(Action(ActionType.PLACE, placed_cards=[]))
        self.assertFalse(node.no_place_action())
