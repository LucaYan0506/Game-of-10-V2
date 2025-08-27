from typing import List
from api.models import Game
import json


'''
GameState (lightweight dataclass)
'''


class GameState:
    board: list[list[str]]
    pool: str
    creator_cards: List[str]
    opponent_cards: List[str]
    creator_point: int
    opponent_point: int
    creator_turn: bool
    winner = str
    tie = bool

    def __init__(self, game: Game):
        self.board = json.loads(game.board)
        self.pool = game.pool
        self.creator_cards = json.loads(game.creator_cards)
        self.opponent_cards = json.loads(game.opponent_cards)
        self.creator_point = game.creator_point
        self.opponent_point = game.opponent_point
        self.creator_turn = game.creator_turn
        self.winner = ''
        self.tie = False
