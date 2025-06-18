from .models import Game
from functools import cmp_to_key


BOARD_HEIGHT = 13
BOARD_WIDTH = 13

OPERATION = {
    'ADD':'+',
    'MUL':'x',
    'SUB':'-',
    'DIV':'/',
} 

ALLOPERATION = "+-/x"
"""
cardPlaced = [
    {
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
                break
            if card['i'] != firstCard['i']:
                isHorizontal = False
                break

        # check if op is at the start or end
        if cardPlaced[0]['val'] in ALLOPERATION or cardPlaced[-1]['val'] in ALLOPERATION:
            return "INVALID"
        # check if 2 op are together
        for i in range(len(cardPlaced) - 1):
            if cardPlaced[i]['val'] in ALLOPERATION and cardPlaced[i + 1]['val'] in ALLOPERATION:
                return "INVALID"

        if isHorizontal:
            for i in range(len(cardPlaced) - 1):
                if cardPlaced[i + 1]['j'] - cardPlaced[i]['j'] != 1:
                    return "INVALID"
            return "HORIZONTAL"
        if isVertical:
            for i in range(len(cardPlaced) - 1):
                if cardPlaced[i + 1]['i'] - cardPlaced[i]['i'] != 1:
                    return "INVALID"
            return "VERTICAL"

        return "INVALID"
    
    cardPlaced = sorted(cardPlaced, key=lambda x: x['j'])
    res1 = helper(cardPlaced)
    cardPlaced = sorted(cardPlaced, key=lambda x: x['j'])
    res2 = helper(cardPlaced)
    if res1 != "INVALID":
        return res1
    
    if res2 != "INVALID":
        return res2

    return "INVALID"

def calculateEquation(equationStr:str):
    equation = []
    num = 0
    res = 0
    for x in equationStr:
        if x in ALLOPERATION:
            equation.append(num)
            equation.append(x)
            num = 0
        else:
            num = num * 10 + int(x)
    equation.append(num)

    # equation without /*
    newEquation = []
    i = 0
    while i < len(equation):
        if equation[i] == OPERATION['DIV']:
            val = newEquation[-1] / equation[i + 1]
            newEquation[-1] = val
            i += 2
        elif equation[i] == OPERATION['MUL']:
            val = newEquation[-1] * equation[i + 1]
            newEquation[-1] = val
            i += 2
        else:
            newEquation.append(equation[i])
            i += 1

    res = 0
    op = 1
    for x in newEquation:
        if isinstance(x,int):
            res += x * op
        else:
            op = 1 if (x == OPERATION['ADD']) else -1
    

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

def isCreator(user, game):
    return game in user.created_games.all()

def get_my_cards(user, game):
    if isCreator(user, game):
        return game.creator_cards

    return game.opponent_cards

def is_my_turn(user, game):
    return isCreator(user, game) == game.creator_turn
    
def get_my_score(user, game):
    if isCreator(user, game):
        return game.creator_point
    return game.opponent_point

def get_enemy_score(user, game):
    if isCreator(user, game):
        return game.opponent_point
    return game.creator_point