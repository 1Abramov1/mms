from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('clients/', include('apps.clients.urls')),
    path('', RedirectView.as_view(url='clients/')),
    path('messages/', include('apps.mailing_messages.urls')),
    path('mailings/', include('apps.mailings.urls')),
]

