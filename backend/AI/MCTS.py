from django.test import Client
import math, random, json
from api.utils import is_valid_action, discard_card, update_game_state
from itertools import permutations
from django.db import close_old_connections
from asgiref.sync import async_to_sync
from api.models import Game
from copy import deepcopy
import itertools

empty_board  = [[None for _ in range(13)] for _ in range(13)]

# Const values
C = 1/math.sqrt(2)
CARDS_SIZE = 6

"""
action = [
    {
        id: ,
        val: ,
        i: ,
        j: ,

    }
]
"""

class Game_State:
    def __init__(self, board=None, user_cards=None, score=0):
        self.board = board if board else empty_board
        self.user_cards = user_cards if user_cards else []
        self.score = score

    def game_is_end(self):
        return self.score >= 20

    def copy(self):
        return Game_State(board=deepcopy(self.board),
                          user_cards=self.user_cards[:],
                          score=self.score)

    def _candidate_lines(self):
        # return all horizontal and vertical lines
        lines = []
        for r in range(13):
            lines.append([self.board[r][c] for c in range(13)])  # horizontal
        for c in range(13):
            lines.append([self.board[r][c] for r in range(13)])  # vertical
        return lines

    def _find_blanks(self, line):
        return [i for i, cell in enumerate(line) if cell == None]

    def _valid_fills(self, line, blanks):
        # prune: only fill up to 3 blanks at a time
        if not blanks:
            return []

        max_fill = min(3, len(blanks), len(self.user_cards))
        fills = []

        # try all combinations of cards for the selected number of blanks
        for num_fill in range(1, max_fill+1):
            for cards_comb in itertools.combinations(self.user_cards, num_fill):
                # fill blanks sequentially
                new_line = line[:]


                # change this to what i have in utils
                for idx, card in zip(blanks, cards_comb):
                    new_line[idx] = card
                fills.append(new_line)

        return fills

    def get_potential_actions(self):
        actions = []
        for line in self._candidate_lines():
            blanks = self._find_blanks(line)
            for action in self._valid_fills(line, blanks):
                if is_valid_action(action, self.user_cards, self.board):
                    actions.append(action)
        return actions

class Node:
    def __init__(self, parent, game_state:Game_State = Game_State()):
        self.parent:Node = parent
        self.children = set() # set of tuple (game_state, action to reach that board)
        self.tried_action = set() 
        self.game_state = game_state
        self.q = 0 # reward
        self.n = 0 # number of exploration
        self.a = [] # action

    def is_fully_expanded(self):
        pass #TODO
        
def UCB1(parent:Node, child:Node):
    # in theory, parent.n should never == 0
    extra = 0
    # if child is never visited, increase exploration chance of this childs
    if child.n == 0:
        extra = 1/10000000
    return child.q / child.n + C * math.sqrt(2*math.log(parent.n))/(child.n + extra)

def best_child(node:Node):
    best_node = Node(None, Game_State())
    best_node_ucb = -100000000
    for child in node.children:
        ucb = UCB1(node, child)
        if best_node_ucb < ucb:
            best_node_ucb = ucb
            best_node = child
    
    return best_node


def expand(node:Node):
    valid_actions = node.game_state.get_potential_actions()
    untried_action = []
    for action in valid_actions:
        if action not in node.tried_action:
            untried_action.append(action)
    # get untried action 
    action = untried_action[random.randint(0, len(untried_action) - 1)]
    board = node.game_state.apply_action(action)
    newChild = Node(node, board)
    newChild.a = action

    return newChild
    
    
def tree_policy(node:Node):
    while(node.game_is_end() == False):
        if node.is_fully_expanded() == False:
            return expand(node)
        node = best_child(node)
        
    return node

def default_policy(game_state: Game_State):
    while game_state.game_is_end() == False:
        valid_actions = game_state.get_potential_actions()
        # Note: randint is inclusive on both side
        action = valid_actions[random.randint(0, len(valid_actions) - 1)]  
        game_state.apply_action(action)

    return game_state.score

def back_prop(node:Node, reward:int):
    while node is not None:
        node.n += 1
        node.q += reward
        node = node.parent

def uct_search(board):
    root = Node(None, board)
    budget = 10**5
    while budget > 0:
        node = tree_policy(root)
        # parent has not child
        reward = default_policy(node.game_state)
        back_prop(node,reward)
        budget-=1
    return best_child(root)
    

def play(game_id):
    close_old_connections()  # Important for DB access in new thread

    game = Game.objects.get(game_id=game_id)
    if game.creator_turn:
        print("Not AI's turn")
        return # not ai turn
    
    print("AI is thinking...")
    board = json.loads(game.board) 
    my_cards = json.loads(game.opponent_cards)
    card_placed = uct_search(my_cards, board).a
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