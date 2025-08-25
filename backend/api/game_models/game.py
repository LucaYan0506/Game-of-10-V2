from .action import Action
from typing import List
import json, random
from api.models import Game
from .. import game_config

class GameLogic:
  '''
    Controls the main logic of the game
  '''
  
  def update(self,game:Game, action: Action, my_cards: List[str], is_creator_turn: bool, save_to_database:bool = True):
    board = json.loads(game.board) 
    point = sum([card.val in game_config.OPERATORS for card in action.placed_cards])

    for card in action.placed_cards:
        board[card.i][card.j] = card.val
        my_cards[card.id] = self.generate_new_card(game, want_number=('0' <= card.val <= '9'))
    
    game.board = json.dumps(board)

    if is_creator_turn:
        game.creator_turn = False
        game.creator_cards = json.dumps(my_cards)
        game.creator_point += point
    else:
        game.creator_turn = True
        game.opponent_cards = json.dumps(my_cards)
        game.opponent_point += point
    
    if save_to_database:
      game.save()
  
  def discard(self, game:Game, user_cards, selectedCardIndex, is_creator_turn, save_to_database:bool = True):
    user_cards[selectedCardIndex] = self.generate_new_card(game, want_number=('0' <= user_cards[selectedCardIndex] <= '9'))

    if is_creator_turn:
        game.creator_cards = json.dumps(user_cards)
    else:
        game.opponent_cards = json.dumps(user_cards)
    
    game.creator_turn = not is_creator_turn

    if save_to_database:
      game.save()
  
  def generate_new_card(self, game:Game, want_number, save_to_database:bool = True):
    which = -1
    for i, x in enumerate(game.pool):
      if x < '0' or x > '9':
          which = i
          break 
      
    if want_number:
      k = random.randint(0, which-1)
    else:
      k = random.randint(which, len(game.pool)-1)
    
    pool = game.pool
    newCard = pool[k]
    pool = pool[:k] + pool[k+1:]
    game.pool = pool
    if save_to_database:
      game.save()
    return newCard
  
  def game_is_end(self, game):
    return game.creator_point >= 20 or game.opponent_point >= 20
