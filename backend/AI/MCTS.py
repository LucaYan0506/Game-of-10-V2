import math, random, json
from django.db import close_old_connections
from asgiref.sync import async_to_sync
from api.models import Game
from api.game_models.game import GameLogic 
from api.game_models.game_state import GameState 
from api.game_models.action import Action 
from api.game_config import BOARD_HEIGHT, BOARD_WIDTH, CARDS_SIZE, EMPTY_BOARD
from AI.hard_codedv1 import find_empty_spot

empty_board  = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]

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
        self.a = Action([]) # action used to get from parent to this node

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
    best_node = Node(None, GameState())
    best_node_ucb = -100000000
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
    action = untried_action[random.randint(0, len(untried_action) - 1)]
    newChild = Node(node, node.game_logic.game, is_creator=not node.is_creator)
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
        action = valid_actions[random.randint(0, len(valid_actions) - 1)]  
        node.game_logic.update(action)

    return node.game_logic.game.score

def back_prop(node:Node, reward:int):
    while node is not None:
        node.n += 1
        node.q += reward
        node = node.parent

def uct_search(game:Game, is_creator:bool)->Action:
    root = Node(None, GameState(game), is_creator=is_creator)
    budget = 10**4
    while budget > 0:
        node = tree_policy(root)
        reward = default_policy(node)
        back_prop(node,reward)
        budget-=1
    return best_child(root).a

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
        print("MCTS is thinking...")
        # time.sleep(2)
    

    board = json.loads(game.board) 
    my_cards = json.loads(game.creator_cards if is_creator else game.opponent_cards)
    action = uct_search(game, is_creator=is_creator)
    
    if log:
        print("AI try to place cards at ", action.placed_cards)
    is_valid, _ = action.is_valid_action(my_cards=my_cards, board=board)
    
    if is_valid:
        if log:
            print("Card placed, update DB")
        game_logic.update(action)
    else:
        if log:
            print("Invalid action, AI is going to discard a random card")
        selectedCardIndex = random.randint(0, CARDS_SIZE - 1)
        game_logic.discard(selectedCardIndex)

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
