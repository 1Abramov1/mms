from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from apps.mailings.views import home  # импортируем view главной страницы

urlpatterns = [
    path('admin/', admin.site.urls),
    path('clients/', include('apps.clients.urls')),
    path('', home, name='home'),  # главная страница
    path('messages/', include('apps.mailing_messages.urls')),
    path('mailings/', include('apps.mailings.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
]

