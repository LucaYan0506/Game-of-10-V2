from django.urls import path
from .views import *

urlpatterns = [
    path('', index_view, name="index"),
    path('getCRSF/', get_csrf, name="get_csrf"),
    path('login/', login_view, name="login"),
    path('logout/', logout_view, name="logout"),
    path('session/', session_view, name="session"),
]
