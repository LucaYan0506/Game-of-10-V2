import math, json
from api.utils import discard_card, is_valid_action, update_game_state
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
    card_placed = get_card_to_place(my_cards, board)
    print("AI try to place cards at ", card_placed)

    if is_valid_action(card_placed=card_placed, my_cards=my_cards, board=board):
        print("Card placed, update DB")
        update_game_state(card_placed, my_cards, game, False)
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

def find_empty_spot(card_placed, board):
    size = len(card_placed) + 2
    
    # if any row has empty continues cells of lenght 'size', place card there
    for i in range(len(board)):
        row = board[i]
        for start in range(len(row) - size):
            end = start + size
            if all(cell == "" for cell in row[start:end]):
                # update cards
                for k in range(len(card_placed)):
                    card_placed[k]['i'] = i
                    card_placed[k]['j'] = start + k + 1
                return True

    # same for column

    return False

# Main logic for hard coded AI
#   - this bot doesn't take in consideration the board info
#   - just check cards and try to place it on a empty spot
def get_card_to_place(cards, board):
    all_perms = []

    for r in range(1, CARDS_SIZE + 1):
        perms = list(permutations(range(CARDS_SIZE), r))
        all_perms.extend(perms)
    
    # check perms with longer length
    all_perms.sort(reverse=True)

    for perm in all_perms:
        card_placed = []
        for index in perm:
            i = 0
            card_placed.append({
                'j':0,
                'i':i,
                'val':cards[index],
                'id':index
            })

        if is_valid_action(card_placed=card_placed, my_cards=cards, board=json.loads(emptyBoard)):
            response = find_empty_spot(card_placed, board)
            if response: # if empty spot found
                return card_placed
            
    return []



'''
from api.models import Game
from AI.hard_coded import play
game = Game.objects.all()[3]
play(game)
'''