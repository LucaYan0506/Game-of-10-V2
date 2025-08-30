from api.game_models.action import Action, ActionType
import json
import random
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
  
    def update(self, action: Action, rng=None):
        user_cards = self._get_user_cards()
        point = 0
        
        if action.type == ActionType.PLACE:
            board = self.game.board if self.is_simulation else json.loads(self.game.board)
            point = action.estimate_point(user_cards)

            for card in action.placed_cards:
                board[card.i][card.j] = card.val
                try:
                    user_cards[card.id] = self.generate_new_card(want_number=('0' <= card.val <= '9'), rng=rng)
                except:
                    self.game.tie = True
                    user_cards[card.id] = ''
                    
            self.game.board = board if self.is_simulation else json.dumps(board)
        elif action.type == ActionType.DISCARD:
            try:
                user_cards[action.card_index] = self.generate_new_card(want_number=('0' <= user_cards[action.card_index]  <= '9'), rng=rng)
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

    def generate_new_card(self, want_number, rng=None):
        which = -1
        for i, x in enumerate(self.game.pool):
            if x < '0' or x > '9':
                which = i
                break

        if want_number:
            if rng:
                k = rng.randint(0, which-1)
            else:
                k = random.randint(0, which-1)
        else:
            if rng:
                k = rng.randint(which, len(self.game.pool)-1)
            else:
                k = random.randint(which, len(self.game.pool)-1)

        pool = self.game.pool
        newCard = pool[k]
        pool = pool[:k] + pool[k+1:]
        if rng is None:  # don't change pool if i have a custom rng
            self.game.pool = pool
        if not self.is_simulation:
            self.game.save()
        return newCard

    def game_is_end(self):
        return self.game.creator_point >= 20 or self.game.opponent_point >= 20 or self.game.tie

    def get_potential_actions(self, n_actions: int = 10000, alpha=0.1):
        actions = set()

        user_cards = self._get_user_cards()
        board = self._get_board()

        # Connecting actions (board + hand)
        lines = self._candidate_lines()
        random.shuffle(lines)
        for line in lines:
            blanks = self._find_blanks(board, line)
            if len(blanks) == 13:
                continue
            for action in self._valid_fills(board, user_cards, blanks, n_actions*0.6 - len(actions)):
                score = action.estimate_point(user_cards)
                score += score * random.uniform(-alpha, alpha)  # ±alpha noise
                actions.add((action, score))
            if len(actions) >= int(n_actions*0.6):
                break

        # Independent actions (ignore board)
        for cards_index in self._select_card_from_hand():
            action = Action(type=ActionType.PLACE, placed_cards=[])
            for i, index in enumerate(cards_index):
                action.placed_cards.append(
                    Card(0, i, user_cards[index], index)
                )
            is_valid, _ = action.is_valid_action(my_cards=user_cards, board=json.loads(EMPTY_BOARD))
            if is_valid:
                response = self._find_empty_spot(action, board)
                if response:
                    score = action.estimate_point(user_cards)
                    score += score * random.uniform(-alpha, alpha)  # ±alpha noise
                    actions.add((action, score))
            if len(actions) >= int(n_actions*1.2):
                break
        
        for i in range(CARDS_SIZE):
            action = Action(type=ActionType.DISCARD, card_index=i)
            actions.add((action, random.random()))  # low priority

        sorted_actions = sorted(actions, key=lambda x: x[1], reverse=True)

        return [action for action, _ in sorted_actions[:n_actions]]

    # helper function 
    def _get_user_cards(self):
        raw_cards = self.game.creator_cards if self.game.creator_turn else self.game.opponent_cards
        return raw_cards if self.is_simulation else json.loads(raw_cards)

    def _get_board(self):
        return self.game.board if self.is_simulation else json.loads(self.game.board)

    def _candidate_lines(self) -> list[list[tuple[int, int]]]:
        # return all horizontal and vertical lines
        lines = []
        for i in range(BOARD_HEIGHT):
            lines.append([(i, j) for j in range(13)])  # horizontal
        for j in range(BOARD_WIDTH):
            lines.append([(i, j) for i in range(13)])  # vertical
        return lines

    def _find_blanks(self, board, line: list[tuple[int, int]]) -> list[tuple[int, int]]:
        return [(i, j) for (i, j) in line if board[i][j] == None or board[i][j] == '']

    def _valid_fills(self, board, user_cards, blanks: list[tuple[int, int]], n_actions=1000000) -> list[Action]:
        # prune: only fill up to 3 blanks at a time
        if not blanks:
            return []

        max_fill = min(6, len(blanks), len(user_cards))  # TODO: avoid using magic number
        potentialAction: set[Action] = set()

        # try some combinations of cards for the selected number of blanks
        num_fills = [i for i in range(1, max_fill+1)]
        random.shuffle(num_fills)
        for num_fill in num_fills:
            # sliding window among blanks with cycles
            n = len(blanks)
            blanks = blanks + blanks

            range_n = [i for i in range(n)]
            random.shuffle(range_n)
            for k in range_n:
                curr_blanks = blanks[k:]
                curr_blanks = curr_blanks[:n]
                for i in range(100):
                    place_cards = random.sample(range(CARDS_SIZE), k=num_fill)
                    cardsToPlace: list[Card] = []
                    for (i, j), cardID in zip(curr_blanks, place_cards):
                        # change the ways to get blanks. e.g. [none, none, 1+0,None...] i can add x1234 after 0, istead of trying to fill the first 2 blank
                        cardsToPlace.append(Card(i=i, j=j, val=user_cards[cardID], id=cardID))
                    action = Action(ActionType.PLACE, placed_cards=cardsToPlace)
                    is_valid, _ = action.is_valid_action(user_cards, board)
                    if is_valid:
                        potentialAction.add(action)
                        if len(potentialAction) >= n_actions:
                            return potentialAction

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

    def _find_empty_spot(self, action:Action, board):
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
    