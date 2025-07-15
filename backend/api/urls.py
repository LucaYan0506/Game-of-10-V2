from django.urls import path
from .views import *

urlpatterns = [
    path('', index_view, name="index"),
    #auth
    path('login/', login_view, name="login"),
    path('logout/', logout_view, name="logout"),
    path('session/', session_view, name="session"),

    path('newGame/', newGame_view, name="newGame"),
    path('hasActiveGame/', hasActiveGame_view, name="hasActiveGame"),
    path('placeCard/', placeCard_view, name="placeCard"),
    path('discardCard/', discardCard_view, name="discardCard"),
    path('gameInfo/', gameInfo_view, name="gameInfo"),
    path('endGame/', endGame_view, name="endGame"),
    path('test/', test_view, name="test"),
]
