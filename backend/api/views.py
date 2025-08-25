from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from AI import hard_codedv3
from .models import Game
from .game_models.game import GameLogic 
from .game_models.card import Card 
from .game_models.action import Action 
import json
from nanoid import generate
from django.core.exceptions import ValidationError 
from .utils import *
from AI import RL, MCTS
import threading


game_logic = GameLogic() # work as a service

# Create your views here.
def index_view(request):
    return render(request,"404page.html")

@require_POST
def login_view(request):
    if request.user.is_authenticated:
        return JsonResponse({'msg': 'User already logged in.'}, status=400)

    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')
    if username is None or password is None:
        return JsonResponse({'msg': 'Username and password cannot be empty.'}, status=400)

    user = authenticate(username=username, password=password)
    if user is None:
        return JsonResponse({'msg': 'Username or password you entered is incorrect.'}, status=400)

    login(request, user)
    return JsonResponse({'msg': 'Successfully logged in.'})

def logout_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'msg': 'You\'re not logged in.'}, status=400)

    logout(request)
    return JsonResponse({'msg': 'Successfully logged out.'})

@ensure_csrf_cookie
def session_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'isAuthenticated': False})

    return JsonResponse({'isAuthenticated': True})

@require_POST
def newGame_view(request):
    # TASK: this need to be changed, if request.user.is_authenticated == False: create guest user
    if not request.user.is_authenticated:
        return JsonResponse({'msg': 'User is not logged in.'}, status=401)

    if has_active_game(request.user):
        return JsonResponse({'msg': 'User already joined a game, please finish or leave that game first'}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'msg': 'Invalid JSON format'}, status=400)
    
    game_id=generate(size=10)
    game_type = Game.get_value_from_label(data.get('gameType'), Game.GameType) 
    game_mode = Game.get_value_from_label(data.get('gameMode'), Game.GameMode)  
    pvp_choice = data.get('pvpChoice')
    status = Game.GameStatus.WAITING

    # make sure that game_id is unique
    while len(Game.objects.filter(game_id=game_id)) >= 1:
        game_id=generate(size=10)

    if not all([game_type, game_mode, pvp_choice]):
        return JsonResponse({'msg': 'Missing required fields: gameType, gameMode, pvpChoice'}, status=400)

    if pvp_choice == 'create':
        ai_model_value = None
        # Only consider an ai_model if the game_mode is PvAi
        if game_mode == Game.GameMode.PVAI:
            ai_model_value = data.get('aiModel')
            if not ai_model_value:
                return JsonResponse({'msg': 'aiModel is required for PvAi games'}, status=400)
            status = Game.GameStatus.ACTIVE
        game = Game(
            game_id=game_id,
            game_type=game_type,
            game_mode=game_mode,
            status=status,
            creator=request.user,
            ai_model=ai_model_value,
            creator_cards = json.dumps([]),
            opponent_cards = json.dumps([]),
        )
        game.creator_cards = json.dumps([game_logic.generate_new_card(game, want_number=(i < 4)) for i in range(6)])
        game.opponent_cards = json.dumps([game_logic.generate_new_card(game, want_number=(i < 4)) for i in range(6)])
        
        try:
            game.full_clean()
            game.save()
            
            return JsonResponse({
                'msg': 'Game created successfully',
                'game_id': game.game_id
            }, status=201)

        except ValidationError as e:
            print(f"Validation Error: {e.message_dict}")
            return JsonResponse({'errors': e.message_dict}, status=400)
    elif pvp_choice == 'join':
        game_id= data.get('gameID')
        if len(Game.objects.filter(game_id=game_id)) < 1:
            print("invalid game id")
            return JsonResponse({'errors': 'Game ID is invalid'}, status=400)

        game = Game.objects.get(game_id=game_id)

        if game.status != Game.GameStatus.WAITING or game.opponent != None:
            print("Unable to join. The game is full")
            return JsonResponse({'msg': 'Unable to join. The game is full'}, status=400)   

        game.opponent = request.user
        game.status = Game.GameStatus.ACTIVE

        try:
            game.full_clean()
            game.save()
            
            return JsonResponse({
                'msg': 'Game joined successfully',
                'game_id': game.game_id
            }, status=201)

        except ValidationError as e:
            print(f"Validation Error: {e.message_dict}")
            return JsonResponse({'errors': e.message_dict}, status=400) 

    return JsonResponse({'msg': 'Invalid pvpChoice'}, status=400)

def hasActiveGame_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'msg': False}, status=201)

    if has_active_game(request.user):
        game = get_active_game(request.user)
        return JsonResponse({
                'msg': has_active_game(request.user),
                'game':{
                    'board': game.board,
                    'my_cards': get_my_cards(request.user, game),
                    'is_my_turn': is_my_turn(request.user, game),
                    'my_score': get_my_score(request.user, game),
                    'enemy_score': get_enemy_score(request.user, game),
                }
            },status=201)
    return JsonResponse({'msg': has_active_game(request.user)}, status=201)
    
@require_POST
def placeCard_view(request):
    # TASK: this need to be changed, if request.user.is_authenticated == False: create guest user
    if not request.user.is_authenticated:
        return JsonResponse({'msg': 'User is not logged in.'}, status=401)

    if has_active_game(request.user) == False:
        return JsonResponse({'msg': "User doesn't have active game."}, status=401)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'msg': 'Invalid JSON format'}, status=400)
    
    game = get_active_game(request.user)
    board = json.loads(game.board) 
    
    if game.game_mode == Game.GameMode.PVP and is_creator(request.user, game) and game.opponent is None:
        return JsonResponse({'msg': "Waiting for opponent to join"}, status=401)

    if not is_my_turn(request.user, game):
        return JsonResponse({'msg': "It's the opponent's turn"}, status=401)
    
    cardPlacedDict = json.loads(data.get('cardPlaced')) 
    action = Action([Card(d["i"], d["j"], d["val"], d["id"]) for d in cardPlacedDict])
    my_cards = json.loads(get_my_cards(request.user, game))

    is_valid, err = action.is_valid_action(my_cards, board)

    if not is_valid:
        print(err)
        return JsonResponse({'msg': err}, status=401)
    
    game_logic.update(game, action, my_cards, is_creator(request.user, game))

    
    if game.game_mode == Game.GameMode.PVAI:
        if game.ai_model == Game.AiModel.HARD_CODED:
            threading.Thread(target=hard_codedv3.play, args=(game.game_id,True,), daemon=True).start()
        elif game.ai_model == Game.AiModel.REINFORCEMENT_LEARNING:
            threading.Thread(target=RL.play, args=(game.game_id,True,), daemon=True).start()
        elif game.ai_model == Game.AiModel.MONTE_CARLO:
            threading.Thread(target=MCTS.play, args=(game.game_id,True,), daemon=True).start()
        else:
            return JsonResponse({'msg': "AI model not found"}, status=401)
        
    return JsonResponse({'msg': "Success"}, status=201)

@require_POST
def discardCard_view(request):
    # TASK: this need to be changed, if request.user.is_authenticated == False: create guest user
    if not request.user.is_authenticated:
        return JsonResponse({'msg': 'User is not logged in.'}, status=401)

    if has_active_game(request.user) == False:
        return JsonResponse({'msg': "User doesn't have active game."}, status=401)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'msg': 'Invalid JSON format'}, status=400)

    game = get_active_game(request.user)

    if game.game_mode == Game.GameMode.PVP and is_creator(request.user, game) and game.opponent is None:
        return JsonResponse({'msg': "Waiting for opponent to join"}, status=401)

    if is_my_turn(request.user, game) == False:
        return JsonResponse({'msg': "It's your turn"}, status=401)

    user_cards = json.loads(get_my_cards(request.user, game))

    selectedCardIndex = json.loads(data.get('selectedCardId')) 
    if selectedCardIndex < 0 or selectedCardIndex >= len(user_cards):
        return JsonResponse({'msg': 'Invalid JSON format'}, status=400)

    game_logic.discard(game, user_cards, selectedCardIndex, is_creator(request.user, game))
   
    if game.game_mode == Game.GameMode.PVAI:
        if game.ai_model == Game.AiModel.HARD_CODED:
            threading.Thread(target=hard_codedv3.play, args=(game.game_id,True,), daemon=True).start()
        elif game.ai_model == Game.AiModel.REINFORCEMENT_LEARNING:
            threading.Thread(target=RL.play, args=(game.game_id,True,), daemon=True).start()
        elif game.ai_model == Game.AiModel.MONTE_CARLO:
            threading.Thread(target=MCTS.play, args=(game.game_id,True,), daemon=True).start()
        else:
            return JsonResponse({'msg': "AI model not found"}, status=401)

    return JsonResponse({'msg': "Success"}, status=201)


def gameInfo_view(request):
    # TASK: this need to be changed, if request.user.is_authenticated == False: create guest user
    if not request.user.is_authenticated:
        return JsonResponse({'msg': 'You are not logged in, please log in'}, status=401)

    if has_active_game(request.user) == False:
        return JsonResponse({'msg': "You don't have an active game, please create or join one."}, status=404)
    game = get_active_game(request.user)
        
    return JsonResponse({
        'game':{
            'game_id':game.game_id,
            'game_type':game.game_type.capitalize() if game.game_type else None,
            'game_mode':game.game_mode if game.game_mode else None,
            'ai_model':game.ai_model.capitalize() if game.ai_model else None,
            'opponent':get_opponent_username(request.user, game),
        }
    },status=201)

def endGame_view(request):
    # TASK: this need to be changed, if request.user.is_authenticated == False: create guest user
    if request.method != "DELETE":
        return JsonResponse({'msg': 'Invalid method.'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'msg': 'User is not logged in.'}, status=401)

    if has_active_game(request.user) == False:
        return JsonResponse({'msg': "User doesn't have active game."}, status=404)
    
    game = get_active_game(request.user)
    game.status = Game.GameStatus.FINISHED
    game.surrendered_by = request.user
    if is_creator(request.user, game):
        game.winner = game.opponent
    else:
        game.winner = game.creator

    game.save()
    return JsonResponse({"msg":"success"}, status=200)


def test_view(request):
    game = get_active_game(request.user)
    threading.Thread(target=hard_codedv3.play, args=(game.game_id,), daemon=True).start()
    return JsonResponse({
        'msg':'test'
    })
'''
from api.models import Game
from django.contrib.auth.models import User
user = User.objects.all().first()

'''