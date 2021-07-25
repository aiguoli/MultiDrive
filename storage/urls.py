from django.urls import path
from .views import *


urlpatterns = [
    path('', index, name='index'),
    path('tutorial/', tutorial, name='tutorial'),
    path('refresh/<int:drive_id>', refresh_token, name='refresh_token'),
    path('clear/<str:drive_slug>/<path:path>/', clear_cache, name='clear_cache'),
    path('convert/<str:drive_slug>/<path:path>/', convert_file, name='convert_file'),
    path('add_disk/', add_disk, name='add_disk'),
    path('callback/', callback, name='callback'),
    path('disks/', disks, name='disks'),
    path('password/', change_file_password, name='change_file_password'),
    path('delete/<int:drive_id>/<str:file_id>/', delete, name='delete'),
    path('<str:drive_slug>/', list_files, name='list_files'),
    path('<str:drive_slug>/<path:path>/', list_files, name='list_files'),
]
