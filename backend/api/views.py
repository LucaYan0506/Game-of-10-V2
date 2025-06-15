from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Game
import json
from nanoid import generate
from django.core.exceptions import ValidationError 
from .utils import isValidAction, calculateEquation, BOARD_HEIGHT, BOARD_WIDTH, has_active_game, get_active_game
from functools import cmp_to_key


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

    return JsonResponse({'msg': has_active_game(request.user)}, status=201)
    
@require_POST
def placeCard(request):
    # TASK: this need to be changed, if request.user.is_authenticated == False: create guest user
    if not request.user.is_authenticated:
        return JsonResponse({'msg': 'User is not logged in.'}, status=401)

    if has_active_game(request.user) == False:
        return JsonResponse({'msg': "User doesn't have active game."}, status=401)
    
    game = get_active_game(request.user)
    board = json.loads(game.board) 
    placedCard = json.loads(data.get('placedCard')) 

    orientation = isValidAction(placedCard)
    if orientation == "HORIZONTAL":
        sorted(mylist, key=cmp_to_key(lambda item1, item2: item1.j < item2.j))
        i = placeCard[0].i
        equation = ""
        minJ = BOARD_WIDTH + 1
        maxJ = -1
        for x in cardPlaced:
            minJ = min(x.j, minJ)
            maxJ = max(x.j, maxJ)

        for j in range(minJ - 1,0, -1):
            if board[i][j] == ".": #if is not empty
                break
            equation += board[i][j]

        for card in placedCard:
            equation += card
        
        for j in range(maxJ + 1, BOARD_WIDTH):
            if board[i][j] == ".": #if is not empty
                break
            equation += board[i][j]


        res1 = calculateEquation(equation)  
        res2 = calculateEquation(reversed(equation))  
        
        if isinstance(res1, int) == False and isinstance(res2, int) == False:
            return JsonResponse({'msg': "User's equation is invalid'."}, status=401)
        
        point = 0
        for card in placedCard:
            if card.val in ALLOPERATION:
                point += 1
            board[card.i][card.j] = card.val
        game.board = json.dumps(board)
        if isCreator(request.user, game):
            game.creator_point += point
        else:
            game.opponent_point += point

        game.save()
        return JsonResponse({'msg': "Success"}, status=201)
        

    elif orientation == "VERTICAL":
        sorted(mylist, key=cmp_to_key(lambda item1, item2: item1.i < item2.i))
        j = placeCard[0].j
        equation = ""
        minI = BOARD_HEIGHT + 1
        maxI = -1
        for x in cardPlaced:
            minI = min(x.i, minI)
            maxI = max(x.i, maxI)

        for i in range(minI - 1,0, -1):
            if board[i][j] == ".": #if is not empty
                break
            equation += board[i][j]

        for card in placedCard:
            equation += card
        
        for i in range(maxI + 1, BOARD_HEIGHT):
            if board[i][j] == ".": #if is not empty
                break
            equation += board[i][j]


        res1 = calculateEquation(equation)  
        res2 = calculateEquation(reversed(equation))  
        
        if isinstance(res1, int) == False and isinstance(res2, int) == False:
            return JsonResponse({'msg': "User's equation is invalid'."}, status=401)
        
        point = 0
        for card in placedCard:
            if card.val in ALLOPERATION:
                point += 1
            board[card.i][card.j] = card.val
        game.board = json.dumps(board)
        if isCreator(request.user, game):
            game.creator_point += point
        else:
            game.opponent_point += point

        game.save()
        return JsonResponse({'msg': "Success"}, status=201)

    return JsonResponse({'msg': "invalid action"})
    
'''
from api.models import Game
from django.contrib.auth.models import User
user = User.objects.all().first()

'''