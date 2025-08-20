from .action import Action
from typing import List
import json, random
from .. import game_config

class GameLogic:
  '''
    Controls the main logic of the game
  '''
  def __init__(self, game):
    self.game = game 


  def update(self, action: Action, my_cards: List[str], is_creator_turn: bool):
    board = json.loads(self.game.board) 
    point = sum([card.val in game_config.OPERATORS for card in action.placed_cards])

    for card in action.placed_cards:
        board[card.i][card.j] = card.val
        my_cards[card.id] = self.generate_new_card(want_number=('0' <= card.val <= '9'))
    
    self.game.board = json.dumps(board)

    if is_creator_turn:
        self.game.creator_turn = False
        self.game.creator_cards = json.dumps(my_cards)
        self.game.creator_point += point
    else:
        self.game.creator_turn = True
        self.game.opponent_cards = json.dumps(my_cards)
        self.game.opponent_point += point
    
    self.game.save()
  

  def discard(self, user_cards, selectedCardIndex, is_creator_turn):
    user_cards[selectedCardIndex] = self.generate_new_card(want_number=('0' <= user_cards[selectedCardIndex] <= '9'))

    if is_creator_turn:
        self.game.creator_cards = json.dumps(user_cards)
    else:
        self.game.opponent_cards = json.dumps(user_cards)
    
    self.game.creator_turn = not is_creator_turn
    self.game.save()
  

  def generate_new_card(self, want_number):
    which = -1
    for i, x in enumerate(self.game.pool):
      if x < '0' or x > '9':
          which = i
          break 
      
    if want_number:
      k = random.randint(0, which-1)
    else:
      k = random.randint(which+1, len(self.game.pool)-1)
    
    pool = self.game.pool
    newCard = pool[k]
    pool = pool[:k] + pool[k+1:]
    self.game.pool = pool
    self.game.save()
    return newCard
  
