from api.game_models.action import Action, ActionType
import json, random
from api.models import Game
from api.game_models.card import Card
from api.game_models.game_state import GameState
from api.game_config import EMPTY_BOARD, BOARD_HEIGHT, BOARD_WIDTH, CARDS_SIZE
from itertools import permutations
from api.websocket_utils import send_game_update


class GameLogic:
  '''
    Controls the main logic of the game
  '''
  def __init__(self, game:Game | GameState, is_simulation:bool=True):
      self.game = game
      self.is_simulation = is_simulation
  
  def update(self, action: Action):
    user_cards = self._get_user_cards()
    point = 0
    
    if action.type == ActionType.PLACE:
        board = self.game.board if self.is_simulation else json.loads(self.game.board)
        point = action.estimate_point(user_cards)

        for card in action.placed_cards:
            board[card.i][card.j] = card.val
            try:
                user_cards[card.id] = self.generate_new_card(want_number=('0' <= card.val <= '9'))
            except:
                self.game.tie = True
                user_cards[card.id] = ''
                
        self.game.board = board if self.is_simulation else json.dumps(board)
    elif action.type == ActionType.DISCARD:
        try:
            user_cards[action.card_index] = self.generate_new_card(want_number=('0' <= user_cards[action.card_index]  <= '9'))
        except Exception as e:
            self.game.tie = True
            user_cards[action.card_index] = ''


    if self.game.creator_turn:
        self.game.creator_turn = False
        self.game.creator_cards = user_cards if self.is_simulation else json.dumps(user_cards)
        self.game.creator_point += point
    else:
        self.game.creator_turn = True
        self.game.opponent_cards = user_cards if self.is_simulation else json.dumps(user_cards)
        self.game.opponent_point += point

    if not self.is_simulation:
      self.game.save()

    if not self.is_simulation:
        player_type = "creator" if self.game.creator_turn else "opponent"
        send_game_update(self.game.game_id, f"{player_type}_move_completed")

  def generate_new_card(self, want_number):
    which = -1
    for i, x in enumerate(self.game.pool):
      if x < '0' or x > '9':
          which = i
          break 
      
    if want_number:
      k = random.randint(0, which-1)
    else:
      k = random.randint(which, len(self.game.pool)-1)
    
    pool = self.game.pool
    newCard = pool[k]
    pool = pool[:k] + pool[k+1:]
    self.game.pool = pool
    if not self.is_simulation:
      self.game.save()
    return newCard
  
  def game_is_end(self):
    return self.game.creator_point >= 20 or self.game.opponent_point >= 20 or self.game.tie
  
  def get_potential_actions(self, n_actions:int = 1e10):
      user_cards = self._get_user_cards()
      board = self._get_board()

      # Generate CONNECTING ACTIONS (hand + board)
      connecting_actions = []
      for line in self._candidate_lines():
        blanks = self._find_blanks(board, line)
        connecting_actions += self._valid_fills(board, user_cards, blanks) 

      if len(connecting_actions) > (int)(n_actions*0.6):
          connecting_actions = connecting_actions[:(int)(n_actions*0.6)] 
          # TODO instead of taking 30 randomly, take 25 with highest score and 5 randomly
      
      # try every permutation of cards (without considering the info on the board)
      # add up to n_actions
      # 3/4 highest score + 1/4 random
      # Generate INDEPENDENT ACTIONS (from hand only)
      independent_actions = []
      for cards_index in self._select_card_from_hand():
          action = Action(type=ActionType.PLACE, placed_cards= [])
          for i,index in enumerate(cards_index):
              action.placed_cards.append(
                  Card(0,i,user_cards[index], index)
              )
          is_valid, _ = action.is_valid_action(my_cards=user_cards, board=json.loads(EMPTY_BOARD))
          if is_valid:
              response = self._find_empty_spot(action, board)
              if response: # if empty spot found
                  independent_actions.append(action)

      if len(independent_actions) > n_actions - len(connecting_actions):
          connecting_actions = connecting_actions[:n_actions - len(connecting_actions)] 

      # add 2 DISCARD action
      discard_action = [Action(type=ActionType.DISCARD, card_index=i) for i in range(CARDS_SIZE)]
      if n_actions <= 50:
          discard_action = random.sample(discard_action, 2)
          
      all_potential_actions = connecting_actions + independent_actions + discard_action

      return all_potential_actions

  # helper function 
  def _get_user_cards(self):
      raw_cards = self.game.creator_cards if self.game.creator_turn else self.game.opponent_cards
      return raw_cards if self.is_simulation else json.loads(raw_cards)

  def _get_board(self):
    return self.game.board if self.is_simulation else json.loads(self.game.board)

  def _candidate_lines(self)->list[list[tuple[int,int]]]:
      # return all horizontal and vertical lines
      lines = []
      for i in range(BOARD_HEIGHT):
          lines.append([(i,j) for j in range(13)])  # horizontal
      for j in range(BOARD_WIDTH):
          lines.append([(i,j) for i in range(13)])  # vertical
      return lines

  def _find_blanks(self, board, line:list[tuple[int,int]])->list[tuple[int,int]]:
      return [(i,j) for (i,j) in line if board[i][j] == None]

  def _valid_fills(self, board, user_cards, blanks:list[tuple[int,int]])->list[Action]:
      # prune: only fill up to 3 blanks at a time
      if not blanks:
          return []

      max_fill = min(3, len(blanks), len(user_cards)) # TODO: avoid using magic number 3
      potentialAction:list[Action] = []

      # try all combinations of cards for the selected number of blanks
      for num_fill in range(1, max_fill+1):
        for permutation in permutations(range(CARDS_SIZE), num_fill):
            # fill blanks sequentially
            cardsToPlace:list[Card] = []

            for (i,j), cardID in zip(blanks, permutation):
                cardsToPlace.append(Card(i=i,j=j,val=board[i][j],id=cardID))
            action = Action(ActionType.PLACE, placed_cards=cardsToPlace)
            is_valid, _ = action.is_valid_action(user_cards)
            if is_valid:
                potentialAction.append(Action(cardsToPlace))

      return potentialAction

  # this func assume self.user_cards[:4] are numbers and self.user_cards[4:6] are op 
  def _select_card_from_hand(self):
      res = []
      #op = 1
      for i in range(1,4):
          for j in range(1, 5 - i):
              perms1 = permutations(range(4),i)
              for cards1ID in perms1:
                  perms2 = permutations([i for i in range(4) if i not in cards1ID],j)
                  for cards2ID in perms2:
                      # 4,5 are the index of op in cards
                      res.append(cards1ID + (4,) + cards2ID) # TODO avoid magic numbers
                      res.append(cards1ID + (5,) + cards2ID)

      # op = 2
      possibleCombs = [
          (1,1,1),
          (2,1,1),
          (1,2,1),
          (1,1,2),
      ]
      for comb in possibleCombs:
          perms1 = permutations(range(4),comb[0])
          for cards1ID in perms1:
              perms2 = permutations([i for i in range(4) if i not in cards1ID],comb[1])
              for cards2ID in perms2:
                  perms3 = permutations([i for i in range(4) if i not in cards2ID],comb[2])
                  for cards3ID in perms3:
                      # 4,5 are the index of op in cards
                      res.append(cards1ID + (4,) + cards2ID + (5,) + cards3ID) # TODO avoid magic numbers
                      res.append(cards1ID + (5,) + cards2ID + (4,) + cards3ID) 
      
      return res

  def _find_empty_spot(self,action:Action, board):
      size = len(action.placed_cards) + 2
      
      # if any row has empty continues cells of lenght 'size', place card there
      for i in range(BOARD_HEIGHT):
          row = board[i]
          for start in range(len(row) - size):
              end = start + size
              if all(cell == "" for cell in row[start:end]):
                  # update cards
                  for k in range(len(action.placed_cards)):
                      action.placed_cards[k].i = i
                      action.placed_cards[k].j = start + k + 1
                  return True

      # same for column
      for j in range(BOARD_WIDTH):
          col = []
          for i in range(BOARD_HEIGHT):
              col.append(board[i][j])

          for start in range(len(col) - size):
              end = start + size
              if all(cell == "" for cell in col[start:end]):
                  # update cards
                  for k in range(len(action.placed_cards)):
                      action.placed_cards[k].i = start + k + 1
                      action.placed_cards[k].j = j
                  return True
              
      return False
