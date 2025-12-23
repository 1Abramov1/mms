from django.contrib import admin
from django.urls import path, include
from apps.mailings.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('apps.users.urls', namespace='users')),  # Ваше приложение
    path('clients/', include('apps.clients.urls')),
    path('', home, name='home'),
    path('messages/', include('apps.mailing_messages.urls')),
    path('mailings/', include('apps.mailings.urls')),
]

