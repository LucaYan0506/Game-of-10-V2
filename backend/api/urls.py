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
]
