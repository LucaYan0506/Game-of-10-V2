import math, random, json
from django.db import close_old_connections
from asgiref.sync import async_to_sync
from api.models import Game
from api.game_models.game import GameLogic 
from api.game_models.card import Card 
from api.game_models.action import Action 
from api.game_config import BOARD_HEIGHT, BOARD_WIDTH, CARDS_SIZE
from copy import deepcopy
import itertools, time

empty_board  = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]

# Const values
C = 1/math.sqrt(2)

class Game_State:
    def __init__(self, board=None, user_cards=None, score=0):
        self.board = board if board else empty_board
        self.user_cards:list[str] = user_cards if user_cards else []
        self.score = score

    def game_is_end(self):
        return self.score >= 20

    def copy(self):
        return Game_State(board=deepcopy(self.board),
                          user_cards=self.user_cards[:],
                          score=self.score)

    def _candidate_lines(self)->list[list[tuple[int,int]]]:
        # return all horizontal and vertical lines
        lines = []
        for i in range(BOARD_HEIGHT):
            lines.append([(i,j) for j in range(13)])  # horizontal
        for j in range(BOARD_WIDTH):
            lines.append([(i,j) for i in range(13)])  # vertical
        return lines

    def _find_blanks(self, line:list[tuple[int,int]])->list[tuple[int,int]]:
        return [(i,j) for (i,j) in line if self.board[i][j] == None]

    def _valid_fills(self, blanks:list[tuple[int,int]])->list[Action]:
        # prune: only fill up to 3 blanks at a time
        if not blanks:
            return []

        max_fill = min(3, len(blanks), len(self.user_cards))
        potentialAction:list[Action] = []

        # try all combinations of cards for the selected number of blanks
        for num_fill in range(1, max_fill+1):
            for permutation in itertools.permutations(range(CARDS_SIZE), num_fill):
                # fill blanks sequentially
                cardsToPlace:list[Card] = []


                # change this to what i have in utils
                for (i,j), cardID in zip(blanks, permutation):
                    cardsToPlace.append(Card(i=i,j=j,val=self.board[i][j],id=cardID))
                potentialAction.append(Action(cardsToPlace))

        return potentialAction

    def get_potential_actions(self):
        actions = []
        for line in self._candidate_lines():
            blanks = self._find_blanks(line)
            for action in self._valid_fills(blanks):
                is_valid, _ = action.is_valid_action(self.user_cards)
                if is_valid:
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
        self.a = Action([]) # action used to get from parent to this node

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
    

def play(game_id, log=False, is_creator = False):
    close_old_connections()  # Important for DB access in new thread

    game = Game.objects.get(game_id=game_id)
    game.refresh_from_db()
    if game.creator_turn != is_creator:
        if log:
            print("Not AI's turn")
        return # not ai turn
    
    if log:
        print("MCTS is thinking...")
    time.sleep(2)
    
    board = json.loads(game.board) 
    my_cards = json.loads(game.creator_cards if is_creator else game.opponent_cards)
    action = uct_search(my_cards, board).a
    
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
    if log: # new arg live, instead of using log
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            game_id,
            {
                'type': 'update',
                'payload': 'ai_action_made'
            }
)
