from .models import Game
import random, json, math
from typing import List

BOARD_HEIGHT = 13
BOARD_WIDTH = 13
POWERS_OF_10 = {10**i for i in range(0, 10)}  # precomputed powers of 10

OPERATOR = {
    'ADD':'+',
    'MUL':'x',
    'SUB':'-',
    'DIV':'/',
} 

OPERATORS = "+-/x"
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

class PlacedCard:
    def __init__(self, i, j, val, id):
        self.i = i
        self.j = j
        self.val = val
        self.id = id

    def __str__(self):
        return f"\n      {self.val} at i={self.i} j={self.j}"

    __repr__ = __str__
class Action:
    def __init__(self, placed_cards: List[PlacedCard]):
        self.placed_cards = placed_cards  # list of PlacedCard


# if action are in the same line (either vertical or horizontal)
def is_line(action:Action):
    if len(action.placed_cards) == 0:
        return "INVALID"
    
    def helper(action:Action):
        firstCard = action.placed_cards[0]
        isHorizontal = True
        isVertical = True
        for card in action.placed_cards:
            #check vertical line
            if card.j != firstCard.j:
                isVertical = False
            if card.i != firstCard.i:
                isHorizontal = False
        
        if isVertical:
            return "VERTICAL"
        if isHorizontal:
            return "HORIZONTAL"

        return "INVALID"
    
    action.placed_cards = sorted(action.placed_cards, key=lambda x: x.j)
    res1 = helper(action)
    action.placed_cards = sorted(action.placed_cards, key=lambda x: x.i)
    res2 = helper(action)
    
    if res1 != "INVALID":
        return res1
    if res2 != "INVALID":
        return res2

    return "INVALID"

def try_construct_equation(action:Action, my_cards, board):
    orientation = is_line(action)
    
    # check that action match with the DB
    for c in action.placed_cards:
        if my_cards[c.id] != c.val:
            print(my_cards[c.id], c.val, "invalid action")
            raise TypeError("Invalid action, card placed by user doesn't match with the DB")
    
    if orientation == "HORIZONTAL":
        action.placed_cards = sorted(action.placed_cards, key=lambda x: x.j)
        i = action.placed_cards[0].i
        equation = ""
        minJ = BOARD_WIDTH + 1
        maxJ = -1
        for x in action.placed_cards:
            minJ = min(x.j, minJ)
            maxJ = max(x.j, maxJ)

        start = minJ
        end = maxJ 

        for j in range(minJ - 1,-1, -1):
            if board[i][j] == "": #if is not empty
                break
            start = j

        for j in range(maxJ + 1, BOARD_WIDTH):
            if board[i][j] == "": #if is not empty
                break
            end = j
        
        for j in range(start, end + 1):
            flag = True
            for card in action.placed_cards:
                if j == card.j:
                    equation += str(card.val)
                    flag = False
            if flag:
                equation += str(board[i][j])
    elif orientation == "VERTICAL":
        action.placed_cards = sorted(action.placed_cards, key=lambda x: x.i)
        j = action.placed_cards[0].j
        equation = ""
        minI = BOARD_HEIGHT + 1
        maxI = -1
        for x in action.placed_cards:
            minI = min(x.i, minI)
            maxI = max(x.i, maxI)

        start = minI
        end = maxI 

        for i in range(minI - 1,-1, -1):
            if board[i][j] == "": #if is not empty
                break
            start = i
        
        for i in range(maxI + 1, BOARD_HEIGHT):
            if board[i][j] == "": #if is not empty
                break
            end = i

        for i in range(start, end + 1):
            flag = True
            for card in action.placed_cards:
                if i == card.i:
                    equation += str(card.val)
                    flag = False
            if flag:
                equation += str(board[i][j])

    else:
        raise TypeError("Invalid action: your equation must be a horizontal or vertical line")

    return equation

def calculate_equation(equation_str:str):
    equation = []
    num = 0
    res = 0
    for x in equation_str:
        if x in OPERATORS:
            equation.append(num)
            equation.append(x)
            num = 0
        else:
            num = num * 10 + int(x)
    equation.append(num)

    # Check if the equation starts or ends with an operator
    if equation_str[0] in OPERATORS or equation_str[-1] in OPERATORS:
        raise TypeError("Equation is invalid: cannot start or end with an operator.")

    # Check for two consecutive operators
    for i in range(len(equation_str) - 1):
        if equation_str[i] in OPERATORS and equation_str[i + 1] in OPERATORS:
            raise TypeError("Equation is invalid: cannot have two operators in a row.")

    # equation without /*
    newEquation = []
    i = 0
    while i < len(equation):
        if equation[i] == OPERATOR['DIV']:
            if equation[i + 1] == 0:
                raise TypeError("Equation is invalid: a number cannot be divided by 0")

            val = newEquation[-1] / equation[i + 1]
            newEquation[-1] = val
            i += 2
        elif equation[i] == OPERATOR['MUL']:
            val = newEquation[-1] * equation[i + 1]
            newEquation[-1] = val
            i += 2
        else:
            newEquation.append(equation[i])
            i += 1

    res = 0
    op = 1

    for x in newEquation:
        if isinstance(x,(int,float)):
            res += x * op
        else:
            op = 1 if (x == OPERATOR['ADD']) else (-1)

    return res

# if the equation is power of 10 (i.e. a valid action)
def is_valid_action(action:Action, my_cards, board, debug=True):
    try:
        equation = try_construct_equation(action, my_cards, board)
        res1 = calculate_equation(equation)
        res2 = calculate_equation(equation[::-1])

        # if res1 > 0:
        #     res1 = math.log10(res1)
        # else:
        #     res1 = 0.1 # since the res of the equation is 0, it is invalid, so consider it as a non-integer res, i.e. invalid
        # if res2 > 0:
        #     res2 = math.log10(res2)
        # else:
        #     res2 = 0.1

    except TypeError as e:
        if debug:
            print(e)
        return False
    
    return res1 in POWERS_OF_10 or res2 in POWERS_OF_10 # if the equation is power of 10, return true

def update_game_state(action:Action, my_cards, game, creator):
    board = json.loads(game.board) 
    point = 0

    for card in action.placed_cards:
        if str(card.val) in OPERATORS:
            point += 1
        board[card.i][card.j] = str(card.val)
        my_cards[card.id] = str(generate_new_card(game, op = str(card.val) in OPERATORS))
    game.board = json.dumps(board)

    if creator:
        game.creator_turn = False
        game.creator_cards = json.dumps(my_cards)
        game.creator_point += point
    else:
        game.creator_turn = True
        game.opponent_cards = json.dumps(my_cards)
        game.opponent_point += point
    
    game.save()

def discard_card(game, user_cards, selectedCardIndex, creator):
    user_cards[selectedCardIndex] = generate_new_card(game, op = str(user_cards[selectedCardIndex]) in OPERATORS)
    if creator:
        game.creator_cards = json.dumps(user_cards)
    else:
        game.opponent_cards = json.dumps(user_cards)
    
    game.creator_turn = not creator

    game.save()

def has_active_game(user):
    res = False
    for game in user.created_games.all():
        if game.status != Game.GameStatus.FINISHED:
            res = True
    for game in user.opponent_games.all():
        if game.status != Game.GameStatus.FINISHED:
            res = True

    return res

def get_active_game(user):
    for game in user.created_games.all():
        if game.status != Game.GameStatus.FINISHED:
            return game
    for game in user.opponent_games.all():
        if game.status != Game.GameStatus.FINISHED:
            return game

    raise Exception("user has not active game")

def is_creator(user, game):
    return game in user.created_games.all()

# assumed that gamemode is PvP
def get_opponent_username(user, game):
    if is_creator(user, game) and game.opponent:
        return game.opponent.username
    
    if not is_creator(user, game) and game.creator:
        return game.creator.username
    
    return ""

def get_my_cards(user, game):
    if is_creator(user, game):
        return game.creator_cards

    return game.opponent_cards

def is_my_turn(user, game):
    return is_creator(user, game) == game.creator_turn
    
def get_my_score(user, game):
    if is_creator(user, game):
        return game.creator_point
    return game.opponent_point

def get_enemy_score(user, game):
    if is_creator(user, game):
        return game.opponent_point
    return game.creator_point

def pool_empty(pool, op):
    for c in pool:
        # if c exists in pool
        if (c in OPERATORS) == op:
            return False
        
    return True

def generate_new_card(game, op = False):
    pool = game.pool

    if pool_empty(pool, op):
        if op: # to avoid infinity rec, generate random cards (ideally we should avoid this)
            return OPERATORS[random.randint(0, 3)]

        return random.randint(0, 9)
    
    i = random.randint(0,len(pool) - 1)
    card = pool[i]

    if (card in OPERATORS) == op:
        pool = pool[:i] + pool[i + 1:]
        game.pool = pool
        game.save()
        return card
    
    return generate_new_card(game, op)