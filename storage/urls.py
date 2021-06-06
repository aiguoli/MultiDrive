from django.urls import path
from .views import *


urlpatterns = [
    path('', index, name='index'),
    path('add_disk/', add_disk, name='add_disk'),
    path('callback/', callback, name='callback'),
    path('disks/', disks, name='disks'),
    path('refresh/<int:drive_id>', refresh, name='refresh'),
    path('<str:drive_slug>/', list_files, name='list_files'),
    path('<str:drive_slug>/<path:path>/', list_files, name='list_files'),
]
