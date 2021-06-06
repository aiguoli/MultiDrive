from django.urls import path
from .views import *


urlpatterns = [
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
]
