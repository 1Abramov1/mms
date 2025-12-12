from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('clients/', include('apps.clients.urls')),
    path('', RedirectView.as_view(url='clients/')),  # Добавляем эту строку
]
