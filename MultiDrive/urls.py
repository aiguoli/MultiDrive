from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.views.static import serve
from django.conf import settings

urlpatterns = [
    re_path('static/(?P<path>.*)', serve, {'document_root': settings.STATIC_ROOT}, name='static'),
    path('admin/', admin.site.urls),
    path('accounts/', include(('account.urls', 'account'), namespace='account')),
    path('favicon.ico', RedirectView.as_view(url='static/img/favicon.ico')),
    path('', include(('storage.urls', "storage"), namespace='storage')),
]
