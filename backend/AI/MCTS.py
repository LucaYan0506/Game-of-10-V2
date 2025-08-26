import math
import random
from django.db import close_old_connections
from api.models import Game
from api.game_models.game import GameLogic 
from api.game_models.game_state import GameState 
from api.game_models.action import Action, ActionType
from api.game_config import BOARD_HEIGHT, BOARD_WIDTH
from copy import deepcopy

empty_board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]

# Const values
C = 1/math.sqrt(2)


class Node:
    def __init__(self, parent, game:GameState, is_creator:bool):
        self.parent:Node = parent
        self.children = set() # set of nodes
        self.tried_action = set() 
        self.is_creator = is_creator
        self.game_logic = GameLogic(game, is_simulation=True)
        self.q = 0 # reward
        self.n = 0 # number of exploration
        self.a = None # action used to get from parent to this node

    def is_fully_expanded(self):
        return len(self.tried_action) == 50 #TODO instead of 50 use a dynamic value
        
    # def apply_action(self, action:Action):
        # self.game_logic.update(action=action)

def UCB1(parent:Node, child:Node):
    # in theory, parent.n should never == 0
    extra = 0
    # if child is never visited, increase exploration chance of this childs
    if child.n == 0:
        extra = 1/10000000
    return child.q / child.n + C * math.sqrt(2*math.log(parent.n))/(child.n + extra)

def best_child(node:Node)->Node:
    best_node = None
    best_node_ucb = -1000000000000000
    for child in node.children:
        ucb = UCB1(node, child)
        if best_node_ucb < ucb:
            best_node_ucb = ucb
            best_node = child
    
    return best_node

def expand(node:Node)->Node:
    valid_actions = node.game_logic.get_potential_actions(n_actions=50) #TODO consider this as params
    untried_action = []
    for action in valid_actions:
        if action not in node.tried_action:
            untried_action.append(action)
    
    # get untried action 
    # # TODO include discard as a valid action
    # if len(untried_action) == 0:
    #     action = 
    action = untried_action[random.randint(0, len(untried_action) - 1)]
    
    newChild = Node(node, game=deepcopy(node.game_logic.game), is_creator=not node.is_creator)
    newChild.game_logic.update(action)
    newChild.a = action
    node.children.add(newChild)

    return newChild
    
def tree_policy(node:Node):
    while(node.game_logic.game_is_end() == False):
        if node.is_fully_expanded() == False:
            return expand(node)
        node = best_child(node)
        
    return node

def default_policy(node: Node):
    while node.game_logic.game_is_end() == False:
        valid_actions = node.game_logic.get_potential_actions()
        # Note: randint is inclusive on both side
        action:Action = valid_actions[random.randint(0, len(valid_actions) - 1)]  
        node.game_logic.update(action)
    
    node.game_logic.game.winner = 'creator' if node.game_logic.game.creator_point >= 20 else 'opponent'

    user = 'creator' if node.is_creator else 'opponent'

    if node.game_logic.game.winner == user:
        return 1
    elif node.game_logic.game.winner == '':
        return 0
    else:
        return -1

def back_prop(node:Node, reward: int):
    while node is not None:
        node.n += 1
        node.q += reward
        node = node.parent

def uct_search(game:Game, is_creator: bool)->Action:
    root = Node(None, GameState(game), is_creator=is_creator)
    budget = 100
    while budget > 0:
        node = tree_policy(root)
        reward = default_policy(node)
        back_prop(node,reward)
        budget-=1
    return best_child(root).a

def play(game_id, log=False, is_creator = False):
    close_old_connections()  # Important for DB access in new thread
    
    game = Game.objects.get(game_id=game_id)
    game_logic = GameLogic(deepcopy(game), is_simulation=False)
    game.refresh_from_db()
    if game.creator_turn != is_creator:
        if log:
            print("Not AI's turn")
        return # not ai turn
    
    if log:
        print("MCTS is thinking...")
    
    action = uct_search(game, is_creator=is_creator)
    if log:
        if action.type == ActionType.PLACE:
            print("AI try to place cards at ", action.placed_cards)
            print("Card placed, update DB")
        elif action.type == ActionType.DISCARD:
            print("No valid PLACE action found, discard a random card")

    game_logic.update(action)
