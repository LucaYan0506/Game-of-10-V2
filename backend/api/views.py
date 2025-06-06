from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Game
import json
from nanoid import generate
from django.core.exceptions import ValidationError 

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

    has_active_game = False
    for game in request.user.created_games.all():
        if game.status != Game.GameStatus.FINISHED:
            has_active_game = True
    for game in request.user.opponent_games.all():
        if game.status != Game.GameStatus.FINISHED:
            has_active_game = True
    if has_active_game:
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

        game = Game(
            game_id=game_id,
            game_type=game_type,
            game_mode=game_mode,
            status=status,
            creator=request.user,
            ai_model=ai_model_value
        )

        try:
            game.full_clean()
            game.save()
            
            return JsonResponse({
                'msg': 'Game created successfully',
                'game_id': game.game_id
            }, status=201)

        except ValidationError as e:
            # --- Return a structured error message ---
            # e.message_dict provides field-specific errors, which is great for APIs
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
            return JsonResponse({'error': 'Unable to join. The game is full'}, status=400)   

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
            # --- Return a structured error message ---
            # e.message_dict provides field-specific errors, which is great for APIs
            print(f"Validation Error: {e.message_dict}")
            return JsonResponse({'errors': e.message_dict}, status=400) 

    return JsonResponse({'error': 'Invalid pvpChoice'}, status=400)


'''
from api.models import Game
from django.contrib.auth.models import User
user = User.objects.all().first()

'''