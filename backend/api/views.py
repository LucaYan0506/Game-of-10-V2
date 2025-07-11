from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Game
import json, math
from nanoid import generate
from django.core.exceptions import ValidationError 
from .utils import *
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
            ai_model=ai_model_value,
            creator_cards = json.dumps([generateNewCard(i >= 4) for i in range(6)]),
            opponent_cards = json.dumps([generateNewCard(i >= 4) for i in range(6)]),
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
    
    if is_creator(request.user, game) and game.opponent is None:
        return JsonResponse({'msg': "Waiting for opponent to join"}, status=401)

    if not is_my_turn(request.user, game):
        return JsonResponse({'msg': "It's the opponent's turn"}, status=401)
    
    cardPlaced = json.loads(data.get('cardPlaced')) 
    orientation = isValidAction(cardPlaced)
    
    # check that cardPlaced match with the DB
    cards = json.loads(get_my_cards(request.user, game))
    for c in cardPlaced:
        if cards[c['id']] != c['val']:
            print(cards[c['id']], c['val'], "invalid action")
            return JsonResponse({'msg': "Invalid action, card placed by user doesn't match with the DB."}, status=401)

    if orientation == "HORIZONTAL":
        cardPlaced = sorted(cardPlaced, key=lambda x: x['j'])
        i = cardPlaced[0]['i']
        equation = ""
        minJ = BOARD_WIDTH + 1
        maxJ = -1
        for x in cardPlaced:
            minJ = min(x['j'], minJ)
            maxJ = max(x['j'], maxJ)

        start = minJ
        end = maxJ 

        for j in range(minJ - 1,-1, -1):
            if board[i][j] == "": #if is not empty
                break
            start = j

        for j in range(maxJ + 1, BOARD_WIDTH):
            if board[i][j] == "": #if is not empty
                break
            end = j
        
        for j in range(start, end + 1):
            flag = True
            for card in cardPlaced:
                if j == card['j']:
                    equation += str(card['val'])
                    flag = False
            if flag:
                equation += str(board[i][j])

    elif orientation == "VERTICAL":
        cardPlaced = sorted(cardPlaced, key=lambda x: x['i'])
        j = cardPlaced[0]['j']
        equation = ""
        minI = BOARD_HEIGHT + 1
        maxI = -1
        for x in cardPlaced:
            minI = min(x['i'], minI)
            maxI = max(x['i'], maxI)

        start = minI
        end = maxI 

        for i in range(minI - 1,-1, -1):
            if board[i][j] == "": #if is not empty
                break
            start = i
        
        for i in range(maxI + 1, BOARD_HEIGHT):
            if board[i][j] == "": #if is not empty
                break
            end = i

        for i in range(start, end + 1):
            flag = True
            for card in cardPlaced:
                if i == card['i']:
                    equation += str(card['val'])
                    flag = False
            if flag:
                equation += str(board[i][j])

    else:
        return JsonResponse({'msg': "invalid action: your equation must be a horizontal or vertical line"}, status=401)
    
    try:
        res1 = calculateEquation(equation)
        res2 = calculateEquation(equation[::-1])

        if res1 > 0:
            res1 = math.log10(res1)
        else:
            res1 = 0.1 # since the res of the equation is 0, it is invalid, so consider it as a non-integer res, i.e. invalid
        if res2 > 0:
            res2 = math.log10(res2)
        else:
            res2 = 0.1

    except TypeError as e:
        print(e)
        return JsonResponse({'msg': str(e)}, status=401)

    if res1.is_integer() == False and res2.is_integer() == False:
        return JsonResponse({'msg': "User's equation is invalid, please make sure that the result of the equation is equal to 10^x."}, status=401)
    
    point = 0
    for card in cardPlaced:
        if str(card['val']) in OPERATORS:
            point += 1
        board[card['i']][card['j']] = str(card['val'])
        cards[card['id']] = str(generateNewCard(op = str(card['val']) in OPERATORS))
    game.board = json.dumps(board)

    if is_creator(request.user, game):
        game.creator_turn = False
        game.creator_cards = json.dumps(cards)
        game.creator_point += point
    else:
        game.creator_turn = True
        game.opponent_cards = json.dumps(cards)
        game.opponent_point += point
    
    game.save()
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

    if is_my_turn(request.user, game) == False:
        return JsonResponse({'msg': "It's your turn"}, status=401)

    user_cards = json.loads(get_my_cards(request.user, game))

    selectedCardIndex = json.loads(data.get('selectedCardId')) 
    if selectedCardIndex < 0 or selectedCardIndex >= len(user_cards):
        return JsonResponse({'msg': 'Invalid JSON format'}, status=400)

    user_cards[selectedCardIndex] = generateNewCard(op = str(user_cards[selectedCardIndex]) in OPERATORS)
    if is_creator(request.user, game):
        game.creator_cards = json.dumps(user_cards)
    else:
        game.opponent_cards = json.dumps(user_cards)
    
    game.creator_turn = not is_creator(request.user, game)

    game.save()

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

'''
from api.models import Game
from django.contrib.auth.models import User
user = User.objects.all().first()

'''