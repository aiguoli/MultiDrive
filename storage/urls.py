from django.urls import path
from .views import *


urlpatterns = [
    path('', index, name='index'),
    path('tutorial/', tutorial, name='tutorial'),
    path('refresh/<int:drive_id>', refresh_token, name='refresh_token'),
    path('clear/<str:drive_slug>/<path:path>/', clear_cache, name='clear_cache'),
    path('add_disk/', add_disk, name='add_disk'),
    path('callback/', callback, name='callback'),
    path('disks/', disks, name='disks'),
    path('delete/', delete, name='delete'),
    path('<str:drive_slug>/', list_files, name='list_files'),
    path('<str:drive_slug>/<path:path>/', list_files, name='list_files'),
]
