import math, json
from api.utils import discard_card, try_construct_equation, calculate_equation, update_game_state
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
    discard = False
    print("AI try to place cards at ", card_placed)

    try:
        equation = try_construct_equation(card_placed, my_cards, board)
        res1 = calculate_equation(equation)
        res2 = calculate_equation(equation[::-1])

        if res1 > 0:
            res1 = math.log10(res1)
        else:
            res1 = 0.1 # since the res of the equation is 0, it is invalid, so consider it as a non-integer res, i.e. invalid
        if res2 > 0:
            res2 = math.log10(res2)
        else:
            res2 = 0.1

    except TypeError as e:
        print(e)
        discard = True
    
    if not discard and res1.is_integer() == False and res2.is_integer() == False:
        discard = True

    if discard:
        print("Invalid action, AI is going to discard a random card")
        selectedCardIndex = random.randint(0, CARDS_SIZE)
        discard_card(game, my_cards, selectedCardIndex, False)
    else:
        print("Card placed, update DB")
        update_game_state(card_placed, my_cards, game, False)

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

        valid  = True
        try:
            equation = try_construct_equation(card_placed, cards, json.loads(emptyBoard))
            # print(equation)
            res1 = calculate_equation(equation)
            res2 = calculate_equation(equation[::-1])

            if res1 > 0:
                res1 = math.log10(res1)
            else:
                res1 = 0.1 # since the res of the equation is 0, it is invalid, so consider it as a non-integer res, i.e. invalid
            if res2 > 0:
                res2 = math.log10(res2)
            else:
                res2 = 0.1

        except TypeError as e:
            valid = False # something wrong happen or the equation is invalid

        if valid and (res1.is_integer() or res2.is_integer()):
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