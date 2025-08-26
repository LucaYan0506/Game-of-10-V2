import json
from api.game_models.game import GameLogic 
from api.game_models.card import Card 
from api.game_models.action import Action, ActionType
from api.game_config import EMPTY_BOARD, BOARD_HEIGHT, BOARD_WIDTH
from api.models import Game
import random
from itertools import permutations
import time
from django.db import close_old_connections
from asgiref.sync import async_to_sync

CARDS_SIZE = 6

# this is only for "testing"

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
        print("Hard_codedv1 is thinking...")
        time.sleep(2)
    

    board = json.loads(game.board) 
    my_cards = json.loads(game.creator_cards if is_creator else game.opponent_cards)
    action = longest_valid_action(my_cards, board)
    
    if log:
        if action.type == ActionType.PLACE:
            print("AI try to place cards at ", action.placed_cards)
            print("Card placed, update DB")
        elif action.type == ActionType.DISCARD:
            print("No valid PLACE action found, discard a random card")

    game_logic.update(action)

def find_empty_spot(action:Action, board):
    size = len(action.placed_cards) + 2
    
    # if any row has empty continues cells of lenght 'size', place card there
    for i in range(BOARD_HEIGHT):
        row = board[i]
        for start in range(len(row) - size):
            end = start + size
            if all(cell == "" for cell in row[start:end]):
                # update cards
                for k in range(len(action.placed_cards)):
                    action.placed_cards[k].i = i
                    action.placed_cards[k].j = start + k + 1
                return True

    # same for column
    for j in range(BOARD_WIDTH):
        col = []
        for i in range(BOARD_HEIGHT):
            col.append(board[i][j])

        for start in range(len(col) - size):
            end = start + size
            if all(cell == "" for cell in col[start:end]):
                # update cards
                for k in range(len(action.placed_cards)):
                    action.placed_cards[k].i = start + k + 1
                    action.placed_cards[k].j = j
                return True
            
    return False

# Main logic for hard coded AI
#   - this bot doesn't take in consideration the board info
#   - just check cards and try to place it on a empty spot
def longest_valid_action(cards, board) ->Action:
    all_perms = []

    for r in range(1, CARDS_SIZE + 1):
        perms = list(permutations(range(CARDS_SIZE), r))
        all_perms.extend(perms)
    
    # check perms with longer length
    all_perms.sort(key=len,reverse=True)

    for perm in all_perms:
        action = Action(type=ActionType.PLACE, placed_cards=[])
        i = 0
        for index in perm:
            action.placed_cards.append(
                Card(0,i,cards[index], index)
            )
            i += 1

        is_valid, _ = action.is_valid_action(my_cards=cards, board=json.loads(EMPTY_BOARD))

        if is_valid:
            response = find_empty_spot(action, board)
            if response: # if empty spot found
                return action
            
   # No valid PLACE action found, so discard random card
    return Action(type=ActionType.DISCARD, card_index=random.randint(0, CARDS_SIZE - 1))
