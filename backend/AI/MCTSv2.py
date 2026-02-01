import torch
import math
import random
import datetime
import os
from django.conf import settings
from django.db import close_old_connections
from api.models import Game
from api.game_models.game import GameLogic
from api.game_models.game_state import GameState
from api.game_models.action import Action, ActionType
from copy import deepcopy
from collections import deque
from AI.model_V1 import ValueNet


SYMBOL_TO_CHANNEL = {
    '0': 0, '1': 1, '2': 2, '3': 3, '4': 4,
    '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    '+': 10,
    '-': 11,
    '/': 12,
    'x': 13,
    '': 14
}


class Node:
    def __init__(self, parent, game: GameState, name='root'):
        self.parent: Node = parent
        self.children = set()  # set of nodes
        self.tried_action = set()
        self.potential_action = []
        self.game_logic = GameLogic(game, is_simulation=True)
        self.q = 0  # reward
        self.n = 0  # number of exploration
        self.a = None  # action used to get from parent to this node
        self.name = name

    def is_fully_expanded(self):
        return len(self.tried_action) == len(self.potential_action)

    def no_place_action(self):
        for action in self.potential_action:
            if action.type == ActionType.PLACE:
                return False
        return True


class MCTSv2:
    def __init__(self, uct_search_budget=20, n_actions=8):
        self.C = 2
        self.uct_search_budget = uct_search_budget
        self.n_actions = n_actions
        self.is_root_creator = False
        self.log = False

    def play(self, game_id, log=False, is_creator=False, rng=None):
        close_old_connections()  # Important for DB access in new thread
        self.is_root_creator = is_creator  # update player prospective
        self.log = log

        game = Game.objects.get(game_id=game_id)
        game_logic = GameLogic(deepcopy(game), is_simulation=False)
        game.refresh_from_db()
        if game.creator_turn != self.is_root_creator:
            if self.log:
                print("Not AI's turn")
            return  # not ai turn

        if self.log:
            print("MCTS is thinking...")

        action = self._uct_search(game)
        if self.log:
            if action.type == ActionType.PLACE:
                print("AI try to place cards at ", action.placed_cards)
                print("Card placed, update DB")
            elif action.type == ActionType.DISCARD:
                print("No valid PLACE action found, discard a random card")

        game_logic.update(action, rng)

# Helper function
    def _UCB1(self, parent: Node, child: Node):
        if child.n == 0:
            q = 0.0
        else:
            # q = child.q / child.n
            q = 1 - (child.q / child.n + 1) / 2

        p = 1.0 / len(child.potential_action)
        u = self.C * p * math.sqrt(parent.n) / (1 + child.n)

        return q + u

    def _uct_search(self, game: Game) -> Action:  # TODO keep the tree used in the prevoius round
        root = Node(None, GameState(game))
        root.potential_action = root.game_logic.get_potential_actions(self.n_actions)
        if root.no_place_action():
            return root.potential_action[0]  # stop earlier no point checking further if the only action is discard card

        time1 = time2 = time3 = datetime.timedelta()
        step = 0
        while step < self.uct_search_budget:
            curr = datetime.datetime.now()
            node = self._tree_policy(root)
            time1 += datetime.datetime.now() - curr

            curr = datetime.datetime.now()
            reward = self._value_net_pred(deepcopy(node.game_logic))
            time2 += datetime.datetime.now() - curr

            curr = datetime.datetime.now()
            self._back_prop(node, reward)
            time3 += datetime.datetime.now() - curr
            step += 1

        if self.log:
            print(f"tree policy time: {time1.total_seconds():.4f}s")
            print(f"default policy time: {time2.total_seconds():.4f}s")
            print(f"back_prop time: {time3.total_seconds():.4f}s")
            lev = 0
            q = deque()
            q.append(root)
            while q:
                lev += 1
                size = len(q)
                print(f"curr level length:{size}")
                while size:
                    size -= 1
                    node: Node = q.popleft()
                    for child in node.children:
                        q.append(child)

            print(f"depth level: {lev}")

        best = max(root.children, key=lambda c: (c.n, c.q))
        # TODO: remove debug printing
        if best.a.type == ActionType.DISCARD and len(root.children) > 6:
            print("something went wrong here, we are discading a card when other action are available \n, so we are saying that discarding is more valuable than placing")
            print("root children")
            for i, child in enumerate(root.children):
                print(f'{i}) child[{i}].q == {child.q} child[{i}].n == {child.n} UCB={self._UCB1(root, child)}')
                print(child.a)

        return best.a

    def _best_child(self, node: Node) -> Node:
        best_node = None
        best_node_ucb = -1000000000000000
        for child in node.children:
            ucb = self._UCB1(node, child)
            if best_node_ucb < ucb:
                best_node_ucb = ucb
                best_node = child
        return best_node

    def _expand(self, node: Node) -> Node:
        curr = datetime.datetime.now()
        untried_action = []

        for action in node.potential_action:
            if action not in node.tried_action:
                untried_action.append(action)

        if len(untried_action) == 0:
            print("All potential action")
            for action in node.potential_action:
                print(action)
            print("")
            print("All tried action")
            for action in node.tried_action:
                print(action)

        action = untried_action[random.randint(0, len(untried_action) - 1)]

        newChild = Node(node, game=deepcopy(node.game_logic.game), name=node.name+'->child')
        newChild.game_logic.update(action)
        newChild.potential_action = newChild.game_logic.get_potential_actions(n_actions=self.n_actions)
        newChild.a = action
        node.children.add(newChild)
        node.tried_action.add(action)

        time1 = datetime.datetime.now() - curr
        if self.log:
            print(f"expand time: {time1.total_seconds():.4f}s")

        return newChild

    def _tree_policy(self, node: Node):
        while not node.game_logic.game_is_end():
            if not node.is_fully_expanded():
                return self._expand(node)
            node = self._best_child(node)

        return node

    def _value_net_pred(self, game_logic: GameLogic):
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        raw_board = game_logic._get_board()
        raw_cards = game_logic._get_user_cards()
        score = (game_logic.game.creator_point - game_logic.game.opponent_point) / 20.0
        if not game_logic.game.creator_turn:
            score = -score
        # Note: model_v1 doesn't use stage
        stage = max(game_logic.game.creator_point, game_logic.game.opponent_point) / 20.0

        board = torch.zeros(1, 15, 13, 13, dtype=torch.float32)
        for i in range(13):
            for j in range(13):
                cell = raw_board[i][j]
                ch = SYMBOL_TO_CHANNEL[cell]
                board[0, ch, i, j] = 1.0
        board = board.to(device)
        cards = torch.zeros(1, 14, dtype=torch.float32)
        for ch in raw_cards:
            cards[0, SYMBOL_TO_CHANNEL[ch]] += 1.
        cards = cards.to(device)
        score = torch.tensor(
            [score],
            dtype=torch.float32
        ).unsqueeze(0).to(device)
        stage = torch.tensor(
            [stage],
            dtype=torch.float32
        ).unsqueeze(0).to(device)

        model = ValueNet().to(device)
        model_path = os.path.join(settings.BASE_DIR, "AI/model_weightsV1.pth")
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.eval()
        return model(board, cards, score, stage).detach().cpu().numpy()[0][0]

    def _back_prop(self, node: Node, reward: int):
        while node is not None:
            node.n += 1
            node.q += reward
            node = node.parent
