from json import dumps

BOARD_HEIGHT = 13
BOARD_WIDTH = 13
CARDS_SIZE = 6

OPERATOR = {
    'ADD':'+',
    'MUL':'x',
    'SUB':'-',
    'DIV':'/',
} 
OPERATORS = "+-/x"

EMPTY_BOARD = dumps([[""] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)])

# 20 cards for numbers and 20 for operators
ALL_CARDS = "0123456789" * 20 + OPERATORS * 20