from .models import Game


# Much faster version:
def has_active_game(user):
    return user.created_games.exclude(status=Game.GameStatus.FINISHED).exists() or \
           user.opponent_games.exclude(status=Game.GameStatus.FINISHED).exists()


def get_active_game(user):
    res = [game
           for game in user.created_games.all()
           if game.status != Game.GameStatus.FINISHED] + \
          [game
           for game in user.opponent_games.all()
           if game.status != Game.GameStatus.FINISHED]

    if (len(res) == 0):
        raise Exception("user dont have active game")
    return res[0]


def is_creator(user, game):
    return game in user.created_games.all()


# assumed that gamemode is PvP
def get_opponent_username(user, game):
    if is_creator(user, game) and game.opponent:
        return game.opponent.username

    if not is_creator(user, game) and game.creator:
        return game.creator.username

    return ""


def get_my_cards(user, game):
    if is_creator(user, game):
        return game.creator_cards

    return game.opponent_cards


def is_my_turn(user, game):
    return is_creator(user, game) == game.creator_turn


def get_my_score(user, game):
    if is_creator(user, game):
        return game.creator_point
    return game.opponent_point


def get_enemy_score(user, game):
    if is_creator(user, game):
        return game.opponent_point
    return game.creator_point
