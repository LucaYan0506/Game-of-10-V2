import json
from api.game_models.game import GameLogic 
from api.game_models.action import ActionType
from api.models import Game
from api.game_config import CARDS_SIZE
import time
from django.db import close_old_connections


# Main logic for hard-coded AI - V3
# Combine the logic of V1 and V2, checks which action is better
def play(game_id, log=False, is_creator = False, rng=None):
    close_old_connections()  # Important for DB access in new thread

    game = Game.objects.get(game_id=game_id)
    game_logic = GameLogic(game,is_simulation=False)
    game.refresh_from_db()
    if game.creator_turn != is_creator:
        if log:
            print("Not AI's turn")
        return # not ai turn
    
    if log:
        print("Hard_codedv4 is thinking...")
        time.sleep(2)
    
    # note: to win v3, n_actions >= 500
    action = game_logic.get_potential_actions(n_actions=500, alpha=0)[0]

    if log:
        if action.type == ActionType.PLACE:
            print("AI try to place cards at ", action.placed_cards)
            print("Card placed, update DB")
        elif action.type == ActionType.DISCARD:
            print("No valid PLACE action found, discard a random card")

    game_logic.update(action, rng)
