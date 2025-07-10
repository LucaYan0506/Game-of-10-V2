from .models import Game
import random

BOARD_HEIGHT = 13
BOARD_WIDTH = 13

OPERATOR = {
    'ADD':'+',
    'MUL':'x',
    'SUB':'-',
    'DIV':'/',
} 

OPERATORS = "+-/x"
"""
cardPlaced = [
    {
        id: ,
        val: ,
        i: ,
        j: ,

    }
]
"""
def isValidAction(cardPlaced):
    if len(cardPlaced) == 0:
        return "INVALID"
    
    def helper(cardPlaced):
        firstCard = cardPlaced[0]
        isHorizontal = True
        isVertical = True
        for card in cardPlaced:
            #check vertical line
            if card['j'] != firstCard['j']:
                isVertical = False
            if card['i'] != firstCard['i']:
                isHorizontal = False
        
        # check if 2 op are together
        # for i in range(len(cardPlaced) - 1):
        #     if str(cardPlaced[i]['val']) in OPERATORS and str(cardPlaced[i + 1]['val']) in OPERATORS:
        #         return "INVALID"

        if isHorizontal:
            # for i in range(len(cardPlaced) - 1):
            #     if cardPlaced[i + 1]['j'] - cardPlaced[i]['j'] != 1:
            #         return "INVALID"
            return "HORIZONTAL"
        if isVertical:
            # for i in range(len(cardPlaced) - 1):
            #     if cardPlaced[i + 1]['i'] - cardPlaced[i]['i'] != 1:
            #         return "INVALID"
            return "VERTICAL"

        return "INVALID"
    
    cardPlaced = sorted(cardPlaced, key=lambda x: x['j'])
    res1 = helper(cardPlaced)
    cardPlaced = sorted(cardPlaced, key=lambda x: x['i'])
    res2 = helper(cardPlaced)
    if res1 != "INVALID":
        return res1
    
    if res2 != "INVALID":
        return res2

    return "INVALID"

def calculateEquation(equation_str:str):
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

def generateNewCard(op = False):
    if op:
        return OPERATORS[random.randint(0, 3)]

    return random.randint(0, 9)