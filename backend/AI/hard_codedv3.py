import json
from api.game_models.game import GameLogic 
from api.game_models.action import ActionType
from api.models import Game
from api.game_config import CARDS_SIZE
import random
import time
from django.db import close_old_connections
from asgiref.sync import async_to_sync
from AI.hard_codedv2 import find_action
from AI.hard_codedv1 import longest_valid_action

# Main logic for hard-coded AI - V3
# Combine the logic of V1 and V2, checks which action is better
def play(game_id, log=False, is_creator = False):
    close_old_connections()  # Important for DB access in new thread

    game = Game.objects.get(game_id=game_id)
    game_logic = GameLogic(game,is_simulation=False)
    game.refresh_from_db()
    if game.creator_turn != is_creator:
        if log:
            print("Not AI's turn")
        return # not ai turn
    
    if log:
        print("Hard_codedv3 is thinking...")
        time.sleep(2)
    

    board = json.loads(game.board) 
    my_cards = json.loads(game.creator_cards if is_creator else game.opponent_cards)
    action1 = longest_valid_action(my_cards, board)
    action2 = find_action(my_cards, board)
    action = action1
    if action2.estimate_point(my_cards) > action1.estimate_point(my_cards):
        action = action2

    if log:
        if action.type == ActionType.PLACE:
            print("AI try to place cards at ", action.placed_cards)
            print("Card placed, update DB")
        elif action.type == ActionType.DISCARD:
            print("No valid PLACE action found, discard a random card")

    game_logic.update(action)
