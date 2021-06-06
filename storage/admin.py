from django.contrib import admin
from .models import Drive, WebSettings, Category


admin.site.register([Drive, WebSettings, Category])
