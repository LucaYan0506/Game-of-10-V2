import json
from api.game_models.game import GameLogic 
from api.models import Game
import random
import time
from django.db import close_old_connections
from asgiref.sync import async_to_sync
from AI.hard_codedv2 import find_action
from AI.hard_codedv1 import longest_valid_action

CARDS_SIZE = 6

# Main logic for hard-coded AI - V3
# Combine the logic of V1 and V2, checks which action is better

def play(game_id, log=False, is_creator = False):
    close_old_connections()  # Important for DB access in new thread

    game = Game.objects.get(game_id=game_id)
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
    if action2.estimate_point() > action1.estimate_point():
        action = action2

    if log:
        print("AI try to place cards at ", action.placed_cards)

    
    is_valid, _ = action.is_valid_action(my_cards=my_cards, board=board)

    game_logic = GameLogic(game)
    if is_valid:
        if log:
            print("Card placed, update DB")
        game_logic.update(action, my_cards, is_creator_turn=is_creator)
    else:
        if log:
            print("Invalid action, AI is going to discard a random card")

        selectedCardIndex = random.randint(0, CARDS_SIZE - 1)
        game_logic.discard(my_cards, selectedCardIndex, is_creator_turn=is_creator)

    # send websocket message 
    if log:
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            game_id,
            {
                'type': 'update',
                'payload': 'ai_action_made'
            }
)
    


'''
from api.models import Game
from AI.hard_coded import play
game = Game.objects.all()[3]
play(game)
'''