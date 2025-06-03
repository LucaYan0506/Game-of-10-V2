from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json

# Create your views here.
def index_view(request):
    return render(request,"404page.html")

@ensure_csrf_cookie
def get_csrf(request):
    response = JsonResponse({'detail': 'CSRF cookie set'})
    response['X-CSRFToken'] = get_token(request)
    return response

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
        return JsonResponse({'msg': 'Invalid credentials.'}, status=400)

    login(request, user)
    print(request.user.is_authenticated)
    return JsonResponse({'msg': 'Successfully logged in.'})

def logout_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'You\'re not logged in.'}, status=400)

    logout(request)
    return JsonResponse({'detail': 'Successfully logged out.'})

@ensure_csrf_cookie
def session_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'isAuthenticated': False})

    return JsonResponse({'isAuthenticated': True})
