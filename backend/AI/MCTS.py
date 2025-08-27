import math
import random
import datetime
from django.db import close_old_connections
from api.models import Game
from api.game_models.game import GameLogic
from api.game_models.game_state import GameState
from api.game_models.action import Action, ActionType
from copy import deepcopy
from collections import deque
from time import sleep

class Node:
    def __init__(self, parent, game: GameState, is_creator: bool, name='root'):
        self.parent: Node = parent
        self.children = set()  # set of nodes
        self.tried_action = set()
        self.potential_action = []
        self.is_creator = is_creator
        self.game_logic = GameLogic(game, is_simulation=True)
        self.q = 0  # reward
        self.n = 0  # number of exploration
        self.a = None  # action used to get from parent to this node
        self.name = name

    def is_fully_expanded(self):
        return len(self.tried_action) == len(self.potential_action)


class MCTS:
    def __init__(self, uct_search_budget=100, default_policy_budget=10,
                 win_reward=100, lose_reward=-100, n_actions=50):
        self.C = 1/math.sqrt(2)
        self.uct_search_budget = uct_search_budget
        self.default_policy_budget = default_policy_budget
        self.win_reward = win_reward
        self.lose_reward = lose_reward
        self.n_actions = n_actions

    def play(self, game_id, log=False, is_creator=False):
        close_old_connections()  # Important for DB access in new thread

        game = Game.objects.get(game_id=game_id)
        game_logic = GameLogic(deepcopy(game), is_simulation=False)
        game.refresh_from_db()
        if game.creator_turn != is_creator:
            if log:
                print("Not AI's turn")
            return  # not ai turn

        if log:
            print("MCTS is thinking...")

        action = self._uct_search(game, is_creator=is_creator, log=log)
        if log:
            if action.type == ActionType.PLACE:
                print("AI try to place cards at ", action.placed_cards)
                print("Card placed, update DB")
            elif action.type == ActionType.DISCARD:
                print("No valid PLACE action found, discard a random card")

        game_logic.update(action)

# Helper function
    def _UCB1(self, parent: Node, child: Node):
        # in theory, parent.n should never == 0
        extra = 0
        # if child is never visited, increase exploration chance of this childs
        if child.n == 0:
            extra = 1/10000000
        return child.q / child.n + self.C * math.sqrt(2*math.log(parent.n))/(child.n + extra)

    def _uct_search(self, game: Game, is_creator: bool, log: bool) -> Action:  # TODO keep the tree used in the prevoius round
        root = Node(None, GameState(game), is_creator=is_creator)
        root.potential_action = root.game_logic.get_potential_actions(self.n_actions)
        time1 = time2 = time3 = datetime.timedelta()
        step = 0
        while step < self.uct_search_budget:
            curr = datetime.datetime.now()
            node = self._tree_policy(root)
            time1 += datetime.datetime.now() - curr

            curr = datetime.datetime.now()
            reward = self._default_policy(deepcopy(node.game_logic), node.is_creator)
            time2 += datetime.datetime.now() - curr

            curr = datetime.datetime.now()
            self._back_prop(node, reward)
            time3 += datetime.datetime.now() - curr
            step += 1

        if log:
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
        return self._best_child(root).a

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
        untried_action = []
        for action in node.potential_action:
            if action not in node.tried_action:
                untried_action.append(action)

        action = untried_action[random.randint(0, len(untried_action) - 1)]

        newChild = Node(node, game=deepcopy(node.game_logic.game), is_creator=not node.is_creator, name=node.name+'->child')
        newChild.game_logic.update(action)
        newChild.potential_action = newChild.game_logic.get_potential_actions(n_actions=self.n_actions)
        newChild.a = action
        node.children.add(newChild)
        node.tried_action.add(action)

        return newChild

    def _tree_policy(self, node: Node):
        while not node.game_logic.game_is_end():
            if not node.is_fully_expanded():
                return self._expand(node)
            node = self._best_child(node)

        return node

    def _default_policy(self, game_logic: GameLogic, is_creator: bool):
        steps = 0

        while not game_logic.game_is_end():
            if steps >= self.default_policy_budget:
                return game_logic.game.creator_point if is_creator else game_logic.game.opponent_point

            potential_action = game_logic.get_potential_actions(n_actions=self.n_actions)
            action = random.choice(potential_action)
            game_logic.update(action)
            steps += 1

        user = 'creator' if is_creator else 'opponent'

        if game_logic.game.tie:
            return 0
        elif game_logic.game.winner == user:
            # Reward decreases with steps (win sooner -> higher reward)
            return self.win_reward * (1 - steps / self.default_policy_budget)
        else:
            # Losing sooner is worse
            return self.lose_reward * (1 - steps / self.default_policy_budget)

    def _back_prop(self, node: Node, reward: int):
        while node is not None:
            node.n += 1
            node.q += reward
            node = node.parent
