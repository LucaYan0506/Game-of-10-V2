import math, json
from api.utils import discard_card, is_valid_action, update_game_state, Action, PlacedCard
from api.models import emptyBoard, Game
import random
from itertools import permutations
import time
from django.db import close_old_connections
from asgiref.sync import async_to_sync

CARDS_SIZE = 6

def play(game_id):
    close_old_connections()  # Important for DB access in new thread

    game = Game.objects.get(game_id=game_id)
    if game.creator_turn:
        print("Not AI's turn")
        return # not ai turn
    
    print("AI is thinking...")
    time.sleep(5)

    board = json.loads(game.board) 
    my_cards = json.loads(game.opponent_cards)
    action = longest_valid_action(my_cards, board)

    print("AI try to place cards at ", action.placed_cards)

    if is_valid_action(action=action, my_cards=my_cards, board=board):
        print("Card placed, update DB")
        update_game_state(action, my_cards, game, False)
    else:
        print("Invalid action, AI is going to discard a random card")
        selectedCardIndex = random.randint(0, CARDS_SIZE - 1)
        discard_card(game, my_cards, selectedCardIndex, False)

    # send websocket message 
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        game_id,
        {
            'type': 'update',
            'payload': 'ai_action_made'
        }
)

def find_empty_spot(action:Action, board):
    size = len(action.placed_cards) + 2
    
    # if any row has empty continues cells of lenght 'size', place card there
    for i in range(len(board)):
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

    return False

# Main logic for hard coded AI
#   - this bot doesn't take in consideration the board info
#   - just check cards and try to place it on a empty spot
def longest_valid_action(cards, board):
    all_perms = []

    for r in range(1, CARDS_SIZE + 1):
        perms = list(permutations(range(CARDS_SIZE), r))
        all_perms.extend(perms)
    
    # check perms with longer length
    all_perms.sort(reverse=True)

    for perm in all_perms:
        action = Action([])
        for index in perm:
            i = 0
            action.placed_cards.append(
                PlacedCard(0,i,cards[index], index)
            )

        if is_valid_action(action=action, my_cards=cards, board=json.loads(emptyBoard), debug=False):
            response = find_empty_spot(action, board)
            if response: # if empty spot found
                return action
            
    return []



'''
from api.models import Game
from AI.hard_coded import play
game = Game.objects.all()[3]
play(game)
'''