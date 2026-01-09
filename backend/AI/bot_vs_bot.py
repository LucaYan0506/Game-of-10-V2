import os
import django
import datetime
import argparse
import random
import csv
import json
import importlib
import torch
from tqdm import tqdm
from enum import Enum
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.models import Game
from api.game_models.game import GameLogic
from nanoid import generate
from django.contrib.auth import get_user_model

bot_with_class = ["MCTS"]


class LocalBot(Enum):
    HARD_CODEDv1 = "hard_codedv1"
    HARD_CODEDv2 = "hard_codedv2"
    HARD_CODEDv3 = "hard_codedv3"
    MCTS = "MCTS"
    HARD_CODEDv4 = "hard_codedv4"

    # class-level list of class-based bots

    def load_play_func(self, **bot_kwargs):
        module = importlib.import_module(f"AI.{self.value}")
        if self.value in bot_with_class:
            return lambda *args, **kwargs: module.MCTS(**bot_kwargs).play(*args, **kwargs)
        else:
            return module.play


class Match:
    def __init__(self, game_id: str, bot1: LocalBot, bot2: LocalBot, p1: int, p2: int):
        self.game_id = game_id
        self.bot1 = bot1
        self.bot2 = bot2
        self.p1 = p1
        self.p2 = p2
        self.winner = bot1.value if p1 > p2 else bot2.value


class Summary:
    def __init__(self, batch_id: int, matches: list[Match], time_spent: datetime.timedelta):
        self.batch_id = batch_id
        self.total_matches = len(matches)
        self.matches = matches
        self.time_spent = time_spent
        self.win_counts = self._calculate_wins()

    def _calculate_wins(self) -> dict[str, int]:
        wins = {}
        for match in self.matches:
            winner = match.winner
            wins[winner] = wins.get(winner, 0) + 1
        return wins


RESULTS_DIR = "results"
SUMMARY_FILE = os.path.join(RESULTS_DIR, "summary.csv")
nn_dataset = {
    "boards":   [],
    "cards":   [],
    "outcomes":  [],
    "player_score": [],
    "opp_score": []
}


def get_next_batch_id():
    if not os.path.exists(SUMMARY_FILE):
        return 1

    with open(SUMMARY_FILE, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)

    return len(rows)


def store_data(summary: Summary):
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Save matches
    matches_file = os.path.join(RESULTS_DIR, f"matches_batch_{summary.batch_id}.csv")
    with open(matches_file, "w", newline="") as f:
        writer = csv.writer(f)
        # write header only if file is empty
        writer.writerow(
            [
                "game_id",
                f"{summary.matches[0].bot1.value}_score",
                f"{summary.matches[0].bot2.value}_score",
                "winner",
            ]
        )
        for m in summary.matches:
            writer.writerow([m.game_id, m.p1, m.p2, m.winner])

    # Save summary
    with open(SUMMARY_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if f.tell() == 0:  # file is empty, write header
            header = ["batch_id", "total_matches", "time_spent_seconds"]
            for bot in LocalBot:
                header.append(bot.value)
            writer.writerow(header)

        data = [
            summary.batch_id,
            summary.total_matches,
            int(summary.time_spent.total_seconds()),
        ]

        for bot in LocalBot:
            data.append(summary.win_counts.get(bot.value, 0))

        writer.writerow(data)


def test(bot1: LocalBot, bot2: LocalBot, n_match: int, username, log, same_rng, nn_data_flag) -> list[Match]:
    play1 = bot1.load_play_func()
    play2 = bot2.load_play_func()

    User = get_user_model()
    admin = User.objects.get(username=username)
    matches = []

    for i in tqdm(range(n_match), desc="Running matches"):
        if log:
            print()

        game_id = generate(size=10)
        while len(Game.objects.filter(game_id=game_id)) >= 1:
            game_id = generate(size=10)

        game = Game(
            game_id=game_id,
            game_type=Game.GameType.STANDARD,
            game_mode=Game.GameMode.PVAI,
            status=Game.GameStatus.ACTIVE,
            creator=admin,
            ai_model=Game.AiModel.HARD_CODED,
            creator_cards=json.dumps([]),
            opponent_cards=json.dumps([]),
        )
        game_logic = GameLogic(game=game, is_simulation=False)

        rng1 = None
        rng2 = None
        if same_rng:
            seed = random.randint(1, 100)
            rng1 = random.Random(seed)
            rng2 = random.Random(seed)
        game.creator_cards = json.dumps(
            [game_logic.generate_new_card(want_number=(i < 4), rng=rng1) for i in range(6)],
        )
        game.opponent_cards = json.dumps(
            [game_logic.generate_new_card(want_number=(i < 4), rng=rng2) for i in range(6)]
        )
        game.full_clean()
        game.save()
        if log:
            print(f"Game created. game id:{game_id}")

        local_nn_dataset = {
            "boards":   [],
            "cards":   [],
            "players": [],
            "outcomes":  [],
            "player_score": [],
            "opp_score": []
        }

        # TODO: handle draw case
        while game.creator_point < 20 and game.opponent_point < 20:
            play1(game_id, log=log, is_creator=True, rng=rng1)
            game.refresh_from_db()
            game.creator_turn = not game.creator_turn

            if game.creator_point < 20 and game.opponent_point < 20:
                play2(game_id, log=log, is_creator=False, rng=rng2)

                game.refresh_from_db()
                game.creator_turn = not game.creator_turn

            if nn_data_flag:
                local_nn_dataset["boards"].append(json.loads(game.board))
                local_nn_dataset["cards"].append(json.loads(game.creator_cards))
                local_nn_dataset["players"].append(1)
                local_nn_dataset["player_score"].append(game.creator_point)
                local_nn_dataset["opp_score"].append(game.opponent_point)

                local_nn_dataset["boards"].append(json.loads(game.board))
                local_nn_dataset["cards"].append(json.loads(game.opponent_cards))
                local_nn_dataset["players"].append(-1)
                local_nn_dataset["player_score"].append(game.opponent_point)
                local_nn_dataset["opp_score"].append(game.creator_point)

        game.status = Game.GameStatus.FINISHED
        game.save()

        if nn_data_flag:
            if game.creator_point >= 20:
                for i in range(len(local_nn_dataset["boards"])):
                    local_nn_dataset["outcomes"].append(1*local_nn_dataset["players"][i])
            elif game.opponent_point >= 20:
                for i in range(len(local_nn_dataset["boards"])):
                    local_nn_dataset["outcomes"].append(-1*local_nn_dataset["players"][i])
            else:
                pass  # TODO: draw case

            nn_dataset["boards"] += local_nn_dataset["boards"]
            nn_dataset["cards"] += local_nn_dataset["cards"]
            nn_dataset["outcomes"] += local_nn_dataset["outcomes"]
            nn_dataset["player_score"] += local_nn_dataset["player_score"]
            nn_dataset["opp_score"] += local_nn_dataset["opp_score"]

        if log:
            print(f"{game.creator_point} : {game.opponent_point}")
        matches.append(
            Match(
                game_id=game_id, bot1=bot1, bot2=bot2, p1=game.creator_point, p2=game.opponent_point
            )
        )

    return matches


def main(log, n_matches, bot1: LocalBot, bot2: LocalBot, username, same_rng: bool, nn_data_flag: bool):
    start = datetime.datetime.now()
    matches = test(bot1, bot2, n_matches, username, log, same_rng, nn_data_flag)
    end = datetime.datetime.now()

    delta = end - start
    minutes = delta.seconds // 60
    seconds = delta.seconds % 60

    batch_id = get_next_batch_id()
    summary = Summary(batch_id, matches, delta)
    store_data(summary)

    if log:
        print(f"training time: {minutes}m {seconds}s")
        for winner, count in summary.win_counts.items():
            print(f"{winner} won {count} times")

    if nn_data_flag:
        now = datetime.datetime.now()
        date_str = now.date().isoformat()            
        time_str = now.strftime("%H-%M-%S")
        nn_data_dir = os.path.join("nn_data", date_str)
        os.makedirs(nn_data_dir, exist_ok=True)
        filename = os.path.join(nn_data_dir, f"data_{time_str}.pt")

        print(f"storing nn data at {filename}")
        torch.save({
            "boards": nn_dataset["boards"],
            "cards": nn_dataset["cards"],
            "outcomes": torch.tensor(nn_dataset["outcomes"], dtype=torch.float32),
            "player_score": torch.tensor(nn_dataset["player_score"], dtype=torch.float32),
            "opp_score": torch.tensor(nn_dataset["opp_score"], dtype=torch.float32),
        }, filename)


"""
This script runs a batch of matches between bots and saves the results.

Usage:
    # Run with default settings (100 matches, default bots, log off, username 'admin')
    python AI.bot_vs_bot.py

    # Run with debugging log enabled (prints time and win counts)
    python AI.bot_vs_bot.py --log

    # Run a custom number of matches
    python AI.bot_vs_bot.py --n_matches 200

    # Run with specific bots
    python AI.bot_vs_bot.py --bot1 HARD_CODEDv1 --bot2 HARD_CODEDv2

    # Save matches under a specific username
    python AI.bot_vs_bot.py --username test_user

    # Run with identical RNG seeds for both players (removes card draw randomness, good for fair bot comparison)
    python AI.bot_vs_bot.py --same_rng

    # Run and save data for nn (boards, cards, outcome)
    python AI.bot_vs_bot.py --nn_data
"""
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--same_rng",
        action="store_true",
        help="Use the same RNG seed for both players so they draw identical sequences of cards (removes luck factor).",
    )
    parser.add_argument("--n_matches", type=int, default=100, help="Number of matches to run")
    parser.add_argument("--bot1", type=str, default="HARD_CODEDv1", help="Name of the bot to use")
    parser.add_argument("--bot2", type=str, default="HARD_CODEDv2", help="Name of the bot to use")
    parser.add_argument(
        "--username",
        type=str,
        default="admin",
        help="Username under which to save the matches in the database. "
        "Matches saved under this account will also be visible in live view.",
    )
    parser.add_argument("--nn_data", action="store_true", help="Generate data for nn")

    args = parser.parse_args()
    # Convert bot names to LocalBot values
    try:
        bot1 = getattr(LocalBot, args.bot1)
    except AttributeError:
        raise ValueError(
            f"Unknown bot '{args.bot1}'. Available bots: {[b for b in vars(LocalBot) if not b.startswith('__')]}"
        )
    try:
        bot2 = getattr(LocalBot, args.bot2)
    except AttributeError:
        raise ValueError(
            f"Unknown bot '{args.bot2}'. Available bots: {[b for b in vars(LocalBot) if not b.startswith('__')]}"
        )

    main(
        log=args.log,
        n_matches=args.n_matches,
        bot1=bot1,
        bot2=bot2,
        username=args.username,
        same_rng=args.same_rng,
        nn_data_flag=args.nn_data,
    )
