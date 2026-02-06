from api.game_models.action import Action, ActionType
import json
import random
from api.models import Game
from api.game_models.card import Card
from api.game_models.game_state import GameState
from api.game_config import EMPTY_BOARD, BOARD_HEIGHT, BOARD_WIDTH, CARDS_SIZE
from itertools import permutations
from api.websocket_utils import send_web_socket_message
import datetime

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
            player_type = "opponent" if self.game.creator_turn else "creator"
            send_web_socket_message(self.game.game_id, f"{player_type}_move_completed", "update")

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
        seen = set()
        actions = []

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
                if action not in seen:
                    actions.append((action, score))
                    seen.add(action)
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
                    if action not in seen:
                        actions.append((action, score))
                        seen.add(action)
            if len(actions) >= int(n_actions*1.2):
                break

        for i in range(CARDS_SIZE):
            action = Action(type=ActionType.DISCARD, card_index=i)
            actions.append((action, random.random()))  # low priority

        actions.sort(key=lambda x: x[1], reverse=True)

        return [action for action, _ in actions[:n_actions]]

    # helper function
    def _get_user_cards(self):
        raw_cards = self.game.creator_cards if self.game.creator_turn else self.game.opponent_cards
        return raw_cards if self.is_simulation else json.loads(raw_cards)

    def _get_board(self) -> list[list[str]]:
        return self.game.board if self.is_simulation else json.loads(self.game.board)

    def _candidate_lines(self) -> list[list[tuple[int, int]]]:
        # return all horizontal and vertical lines
        board = self._get_board()
        lines = []
        for i in range(BOARD_HEIGHT):
            horizontal_line = [(i, j) for j in range(BOARD_WIDTH)]

            # if it's not an empty line
            if any([(board[x][y] != '') for (x, y) in horizontal_line]):
                lines.append(horizontal_line)
        for j in range(BOARD_WIDTH):
            vertical_line = [(i, j) for i in range(BOARD_HEIGHT)]

            # if it's not an empty line
            if any([(board[x][y] != '') for (x, y) in vertical_line]):
                lines.append(vertical_line)
        return lines

    def _find_blanks(self, board, line: list[tuple[int, int]]) -> list[tuple[int, int]]:
        return [(i, j) for (i, j) in line if board[i][j] is None or board[i][j] == '']

    def _prune_blanks(self, blanks: list[tuple[int, int]], num_fill) -> tuple[bool, list[tuple[int, int]]]:
        """
        let's say we have _ _ _ _ x _ _, and num_fill = 1. There is no point
        keeping blanks[0], blanks[1], blanks[2], blanks[6] as "candidate" position,
        because those position does not interact with cards in the board.
        Those not interacting potential action interacting with the board is handled
        separately.

        if while pruning we remove blanks[0], then worth_trying=False, because
        there is no point looking for valid action now, as it will be checked later
        when blanks[0] is not removed.
        """

        # cnt[i]=k means that for 0 to k, blanks[i-k+1] - blanks[i-k] = 1
        n = len(blanks)
        cnt = [0] * n
        prev = blanks[0]

        for i in range(1, n):
            cnt[i] = cnt[i-1]
            dist = max(abs(prev[0] - blanks[i][0]), abs(prev[1] - blanks[i][1]))
            prev = blanks[i]

            if dist == 1:
                cnt[i] += 1
            elif dist == 0:
                print("something is wrong, this shouldn't happen")
            else:
                cnt[i] = 0

        cnt_inverse = [0] * n
        prev = blanks[n-1]
        for i in range(n-2, -1, -1):
            cnt_inverse[i] = cnt_inverse[i-1]
            dist = max(abs(prev[0] - blanks[i][0]), abs(prev[1] - blanks[i][1]))
            prev = blanks[i]

            if dist == 1:
                cnt_inverse[i] += 1
            elif dist == 0:
                print("something is wrong, this shouldn't happen")
            else:
                cnt_inverse[i] = 0

        pruned = []
        worth_trying = False
        for i in range(n):
            if cnt[i] < num_fill and cnt_inverse[i] < num_fill:
                if i == 0:
                    worth_trying = True
                pruned.append(blanks[i])

        return worth_trying, pruned

    def _valid_fills(self, board, user_cards, blanks: list[tuple[int, int]], n_actions=1000000) -> list[Action]:
        # prune: only fill up to 3 blanks at a time
        if not blanks:
            return []

        max_fill = min(CARDS_SIZE, len(blanks))
        potentialAction: set[Action] = set()

        # try some combinations of cards for the selected number of blanks
        num_fills = [i for i in range(1, max_fill+1)]
        random.shuffle(num_fills)
        n = len(blanks)
        for num_fill in num_fills:
            # sliding window among blanks
            for k in range(num_fill, n - num_fill):
                curr_blanks = blanks[k:]
                worth_trying, curr_blanks = self._prune_blanks(curr_blanks, num_fill)
                if worth_trying is False:
                    continue
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
    