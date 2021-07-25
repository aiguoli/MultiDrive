from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include(('account.urls', 'account'), namespace='account')),
    path('favicon.ico', RedirectView.as_view(url='static/img/favicon.ico')),
    path('', include(('storage.urls', "storage"), namespace='storage')),
]
