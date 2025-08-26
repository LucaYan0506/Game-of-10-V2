from typing import List, Tuple
from .card import Card
import math, ast, operator
from api import game_config
from enum import Enum
from typing import List, Optional

class ActionType(Enum):
    PLACE = "place"
    DISCARD = "discard"

class Action:
    def __init__(self,type: ActionType,placed_cards: Optional[List[Card]] = None, 
                 card_index: Optional[int] = None):
        
        if not isinstance(type, ActionType):
            raise ValueError(f"Invalid action type: {type}. Must be PLACE or DISCARD.")

        self.type = type

        if type == ActionType.PLACE:
            if placed_cards is None:
                raise ValueError("placed_cards must be provided for PLACE actions")
            self.card_index = None
            self.placed_cards = placed_cards
        elif type == ActionType.DISCARD:
            if card_index is None:
                raise ValueError("card_index must be provided for DISCARD actions")
            self.card_index = card_index
            self.placed_cards = []

    def estimate_point(self, my_cards: List[str]):
        """
        Calculate points including bonus for using all 4 numbers.
        Returns: (base_points, bonus_points, total_points)
        """
        # Base points: 1 point per operator used
        base_points = sum([card.val in game_config.OPERATORS for card in self.placed_cards])
        
        # Check for bonus: +1 if all 4 number cards are used
        number_cards_in_hand = [i for i, card in enumerate(my_cards) if card not in game_config.OPERATORS]
        number_cards_used = [card.id for card in self.placed_cards if card.val not in game_config.OPERATORS]
        
        bonus_points = 0
        # Award bonus if all 4 number cards from hand are used in this action
        if len(number_cards_in_hand) == 4 and len(number_cards_used) == 4:
            if set(number_cards_used) == set(number_cards_in_hand):
                bonus_points = 1
        
        total_points = base_points + bonus_points
        
        return total_points

    # this is only for type=PLACE
    def is_valid_action(self, my_cards, board) -> Tuple[bool, str]:
        if self.type != ActionType.PLACE:
            raise RuntimeError("is_valid_action can only be called for PLACE actions")
        
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
        
        
        check = any(all(x > 0 and is_power_of_ten(x) for x in r) for r in res)
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
    
def is_power_of_ten(value, tolerance=1e-13):
    if value <= 0:
        return False

    log_value = math.log10(value)
    rounded_log = round(log_value)

    # Check if the log value is close to an integer
    return abs(log_value - rounded_log) < tolerance

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
