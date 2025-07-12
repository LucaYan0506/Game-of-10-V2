import math, json, time
from api.utils import is_valid_action, try_construct_equation, calculate_equation, update_game_state
from api.models import emptyBoard
from typing import List, Set, Tuple

CARDS_SIZE = 6

def play(game):
    if game.creator_turn:
        return # not ai turn
    
    time.sleep(10)

    board = json.loads(game.board) 
    card_placed = get_card_to_place(game.opponent_cards, game.board)
    my_cards = json.loads(game.opponent_cards)

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
        return # something wrong happen
    
    if res1.is_integer() == False and res2.is_integer() == False:
        print("User's equation is invalid, please make sure that the result of the equation is equal to 10^x.")
    
    update_game_state(card_placed, my_cards, game, False)
    print(card_placed)

def find_empty_spot(card_placed, board):
    size = len(card_placed) + 2
    
    # if any row has empty continues cells of lenght 'size', place card there
    for row in board:
        for start in range(len(row - size)):
            end = start + size
            if all(cell == [""] for cell in row[start:end]):
                # update cards
                return True

    # same for column

    return False
# Main logic for hard coded AI
#   - this bot doesn't take in consideration the board info
#   - just check cards and try to place it on a empty spot
def get_card_to_place(cards, board):
    allCombination : List[Set[Tuple[int, ...]]] = [{()}]
    
    for i in range(1, CARDS_SIZE + 1):
        prev = allCombination[-1]
        curr = set()
        for comb in prev:
            for j in range(len(cards)):
                if j not in comb:
                    temp = tuple(sorted((*comb, j))) # *comp to unpack comp
                    curr.add(temp)
        
        allCombination.append(curr)

    for combination in allCombination:
        for l in combination:
            card_placed = []
            i = 0
            for index in l:
                card_placed.append({
                    'j':0,
                    'i':i,
                    'val':cards[index]
                })

            valid  = True
            try:
                equation = try_construct_equation(card_placed, cards, json.load(emptyBoard))
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
                valid = False # something wrong happen or the equation is invalid

            if valid and (res1.is_integer() or res2.is_integer()):
                response = find_empty_spot(card_placed, board)
                if response: # if empty spot found
                    return card_placed


    return []

