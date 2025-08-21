from typing import List, Tuple
from .card import Card
from itertools import groupby
import math, ast, operator
from api import game_config

class Action:
    '''
      a list of Card that the player has placed down in their turn
    '''
    def __init__(self, placed_cards: List[Card]):
        self.placed_cards = placed_cards 
    
    def is_valid_action(self, my_cards, board) -> Tuple[bool, str]:
      try:
          equations_set = construct_equations(self.placed_cards, my_cards, board)
      except Exception as e:
          return [False, str(e)]
      
      res = [] 
      err = ""
      for equations in equations_set:
        try:
            res.append([calculate_equation(eq) for eq in equations])
        except Exception as e:
            err = str(e)
      
      if len(res) == 0: # no orientation is good
          return [False, err]
      
      
      check = any(all(x > 0 and math.log10(x).is_integer() for x in r) for r in res)
      return [check, (not check) * "User's equation is invalid, please make sure that the result of the equation is equal to 10^x."]


# ---- helper functions ----
def get_orientation(placed_cards: List[Card]):
    if (len(placed_cards) == 0):
        return "INVALID"
    
    if (all(card.i == placed_cards[0].i for card in placed_cards)):
        return "HORIZONTAL"
    if (all(card.j == placed_cards[0].j for card in placed_cards)):
        return "VERTICAL"
    
    return "INVALID"
    
def construct_equations(placed_cards: List[Card], my_cards: List[str], board: List[List[str]]) -> List[List[str]]:
  # check that action match with the DB
  for c in placed_cards:
      if my_cards[c.id] != c.val:
          print(my_cards[c.id], c.val, "invalid action")
          raise TypeError("Invalid action, card placed by user doesn't match with the DB")
  
  orientation = get_orientation(placed_cards)
  if orientation == "INVALID":
      raise TypeError("Invalid action: your equation must be a horizontal or vertical line")

  deltas = [(orientation == "VERTICAL", orientation == "HORIZONTAL")]
  # special case with 1: both orientation are possible
  if len(placed_cards) == 1:
      deltas.append((orientation == "HORIZONTAL", orientation == "VERTICAL"))
  
  board_copy = [row.copy() for row in board]
  for c in placed_cards:
      board_copy[c.i][c.j] = c.val
  
  ans = []
  for (dx, dy) in deltas:
    care = set()

    for c in placed_cards:
        (x, y) = (c.i, c.j)
        while (0 <= x < game_config.BOARD_HEIGHT and 
                0 <= y < game_config.BOARD_WIDTH and 
                board_copy[x][y] != ""):
            care.add((x, y))
            x += dx 
            y += dy 
        
        (x, y) = (c.i, c.j)
        while (0 <= x < game_config.BOARD_HEIGHT and 
                0 <= y < game_config.BOARD_WIDTH and 
                board_copy[x][y] != ""):
            care.add((x, y))
            x -= dx 
            y -= dy 
    
    care = sorted(list(care))
    prv = care[0] 
    cur = ""
    equations = []

    for (x, y) in care:
        if (x - prv[0] + y - prv[1] <= 1):
            cur += board_copy[x][y]
        else:
            equations.append(cur)
            cur = "" + board_copy[x][y]
        
        prv = (x, y)
    if (len(cur) > 0):
        equations.append(cur)
    ans.append(equations)
    
  return ans
  

def calculate_equation(equation_str: str):
    # kinda resembles haskell style
    equation_str = equation_str.replace("x", "*")
    OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,}

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Constant):
            return node.n
        elif isinstance(node, ast.BinOp):
            return OPS[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            # Only allow a single unary minus
            if isinstance(node.operand, ast.UnaryOp):
                raise ValueError("Multiple unary operators are not allowed")
            return -_eval(node.operand) if isinstance(node.op, ast.USub) else _eval(node.operand)
        else:
            raise ValueError(f"Unsupported expression: {node}")

    node = ast.parse(equation_str, mode='eval')
    return _eval(node.body)
