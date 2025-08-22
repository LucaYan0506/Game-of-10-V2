import os
import django
import datetime
import argparse
import csv
import json
from tqdm import tqdm

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()
from api.models import Game
from AI import hard_codedv1
from AI import hard_coded
from api.game_models.game import GameLogic
from nanoid import generate
from django.contrib.auth import get_user_model

class LocalBot:
    HARD_CODEDv1 = 'hard_codedv1'
    HARD_CODEDv2 = 'hard_coded'

class Match:
    def __init__(self, game_id:str, bot1:LocalBot, bot2:LocalBot, p1, p2):
        self.game_id = game_id 
        self.bot1 = bot1 
        self.bot2 = bot2 
        self.p1 = p1 
        self.p2 = p2
        self.winner = bot1 if p1 > p2 else bot2

class Summary:
    def __init__(self, batch_id:int, matches:list[Match], time_spent:datetime.timedelta):
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

def get_next_batch_id():
    if not os.path.exists(SUMMARY_FILE):
        return 1  

    with open(SUMMARY_FILE, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)

    return len(rows)  

def store_data(summary:Summary):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Save matches
    matches_file = os.path.join(RESULTS_DIR, f"matches_batch_{summary.batch_id}.csv")
    with open(matches_file, "w", newline="") as f:
        writer = csv.writer(f)
        # write header only if file is empty
        writer.writerow(["game_id", f"{summary.matches[0].bot1}_score", f"{summary.matches[0].bot2}_score", "winner"])
        for m in summary.matches:
            writer.writerow([m.game_id, m.p1, m.p2, m.winner])

    # Save summary
    with open(SUMMARY_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if f.tell() == 0:  # file is empty, write header
            header = ["batch_id", "total_matches", "time_spent_seconds"]
            for bot in LocalBot.__dict__:
                if not bot.startswith("__"):  # filter out Python internals
                    header.append(bot)
            writer.writerow(header)

        data = [
            summary.batch_id,
            summary.total_matches,
            int(summary.time_spent.total_seconds()),
        ]

        for bot in LocalBot.__dict__:
            if not bot.startswith("__"):
                bot_name = getattr(LocalBot, bot)
                data.append(summary.win_counts.get(bot_name, 0))

        writer.writerow(data)

def test(bot1:LocalBot, bot2:LocalBot, n_match:int, username, log)->list[Match]:
    if bot1 == LocalBot.HARD_CODEDv1:
        from AI.hard_codedv1 import play as play1
    elif bot1 == LocalBot.HARD_CODEDv2:
        from AI.hard_coded import play as play1

    if bot2 == LocalBot.HARD_CODEDv2:
        from AI.hard_coded import play as play2
    elif bot2 == LocalBot.HARD_CODEDv1:
        from AI.hard_codedv1 import play as play2

    matches = []
    for i in tqdm(range(n_match), desc="Running matches"):
        User = get_user_model()
        admin = User.objects.get(username=username)

        game_id = generate(size=10)
        while len(Game.objects.filter(game_id=game_id)) >= 1:
                game_id=generate(size=10)

        game = Game(
            game_id=game_id,
            game_type=Game.GameType.STANDARD,
            game_mode=Game.GameMode.PVAI,
            status=Game.GameStatus.ACTIVE,
            creator=admin,
            ai_model=Game.AiModel.HARD_CODED,
            creator_cards = json.dumps([]),
            opponent_cards = json.dumps([]),
        )
        game_logic = GameLogic(game)
        game.creator_cards = json.dumps([game_logic.generate_new_card(want_number=(i < 4)) for i in range(6)])
        game.opponent_cards = json.dumps([game_logic.generate_new_card(want_number=(i < 4)) for i in range(6)])

        game.full_clean()
        game.save()
        if log:
            print(f"Game created. game id:{game_id}")

        while game.creator_point < 20 and game.opponent_point < 20:
            play1(game_id, testing=True) #creator
            game.creator_turn = not game.creator_turn
            if game.creator_point < 20:
                play2(game_id, testing=True)
                game.creator_turn = not game.creator_turn
                game.refresh_from_db()

        game.status = Game.GameStatus.FINISHED
        game.save()

        if log:
            print(f'{game.creator_point} : {game.opponent_point}')
            print()
        matches.append(Match(game_id=game_id, bot1=bot1, bot2=bot2, p1=game.creator_point, p2=game.opponent_point))

    return matches

def main(log, n_matches, bot1:LocalBot, bot2:LocalBot, username):
    start = datetime.datetime.now()
    matches = test(bot1,bot2, n_matches, username, log)
    end = datetime.datetime.now()
    
    delta = end - start
    minutes = delta.seconds // 60
    seconds = delta.seconds % 60
    
    batch_id = get_next_batch_id()
    summary = Summary(batch_id, matches, delta)
    store_data(summary)

    if log:
        print(f'training time: {minutes}m {seconds}s') 
        for winner, count in summary.win_counts.items():
            print(f'{winner} won {count} times')


"""
This script runs a batch of matches between bots and saves the results.

Usage:
    # Run with default settings (100 matches, default bots, log off, username 'admin')
    python bot_vs_bot.py

    # Run with debugging log enabled (prints time and win counts)
    python bot_vs_bot.py --log

    # Run a custom number of matches
    python bot_vs_bot.py --n_matches 200

    # Run with specific bots
    python bot_vs_bot.py --bot1 HARD_CODEDv1 --bot2 HARD_CODEDv2

    # Save matches under a specific username
    python bot_vs_bot.py --username test_user
"""
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", action="store_true", help="Enable debug logging")
    parser.add_argument("--n_matches", type=int, default=100, help="Number of matches to run")
    parser.add_argument("--bot1", type=str, default="HARD_CODEDv1", help="Name of the bot to use")
    parser.add_argument("--bot2", type=str, default="HARD_CODEDv2", help="Name of the bot to use")
    parser.add_argument("--username",type=str,default="admin",
                        help="Username under which to save the matches in the database. "
                            "Matches saved under this account will also be visible in live view."
                        )
    args = parser.parse_args()
    # Convert bot names to LocalBot values
    try:
        bot1 = getattr(LocalBot, args.bot1)
    except AttributeError:
        raise ValueError(f"Unknown bot '{args.bot1}'. Available bots: {[b for b in vars(LocalBot) if not b.startswith('__')]}")
    try:
        bot2 = getattr(LocalBot, args.bot2)
    except AttributeError:
        raise ValueError(f"Unknown bot '{args.bot2}'. Available bots: {[b for b in vars(LocalBot) if not b.startswith('__')]}")


    main(
        log=args.log,
        n_matches=args.n_matches,
        bot1=bot1,
        bot2=bot2,
        username=args.username
    )


'''
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
channel_layer = get_channel_layer()
game_id = "prqHFzSRR0"
async_to_sync(channel_layer.group_send)(
    game_id,
    {
        "type": "update",
        "payload": "ai_action_made",
    }
)
'''