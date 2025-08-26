import json
from api.game_models.game import GameLogic 
from api.game_models.card import Card 
from api.game_models.action import Action, ActionType
from api.models import Game
import random
import time
from django.db import close_old_connections
from asgiref.sync import async_to_sync

BOARD_HEIGHT = 13
BOARD_WIDTH = 13
CARDS_SIZE = 6

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
        print("Hard_codedv2 is thinking...")
        time.sleep(2)
    

    board = json.loads(game.board) 
    my_cards = json.loads(game.creator_cards if is_creator else game.opponent_cards)
    action = find_action(my_cards, board)
    
    if log:
        if action.type == ActionType.PLACE:
            print("AI try to place cards at ", action.placed_cards)
            print("Card placed, update DB")
        elif action.type == ActionType.DISCARD:
            print("No valid PLACE action found, discard a random card")

    game_logic.update(action)

# Main logic for hard-coded AI - V2
# for all rows/col, consider some possibilities and see if one fits
def find_action(my_cards, board):
    space1 = [[(i, j) for i in range(BOARD_HEIGHT) if board[i][j] == ""] for j in range(BOARD_WIDTH)]
    space2 = [[(i, j) for j in range(BOARD_WIDTH) if board[i][j] == ""] for i in range(BOARD_HEIGHT)]
    
    best = []
    for coords in space1 + space2:
        for _ in range(100):
            k = random.randint(0, min(len(my_cards), len(coords)))
            where = random.sample(coords, k=k)
            what = random.sample([i for i in range(len(my_cards))], k=k)

            lst = []
            for (l, (i, j)) in enumerate(where):
                lst.append(Card(i, j, my_cards[what[l]], what[l]))
            
            is_valid, _ = Action(type=ActionType.PLACE, placed_cards = lst).is_valid_action(my_cards, board)
            if is_valid and len(lst) > len(best):
                best = lst
                
    if len(best) == 0:
        return Action(type=ActionType.DISCARD, card_index=random.randint(0, CARDS_SIZE - 1))
    return Action(type=ActionType.PLACE, placed_cards= best)
