from django.urls import path
from . import views
from .views import MailingStatisticsView, MailingLogsView, OverallStatisticsView

app_name = 'mailings'

urlpatterns = [

    path('', views.MailingListView.as_view(), name='mailing_list'),
    path('create/', views.MailingCreateView.as_view(), name='mailing_create'),
    path('<int:pk>/', views.MailingDetailView.as_view(), name='mailing_detail'),
    path('<int:pk>/update/', views.MailingUpdateView.as_view(), name='mailing_update'),
    path('<int:pk>/delete/', views.MailingDeleteView.as_view(), name='mailing_delete'),
    path('stats/', views.mailing_stats, name='mailing_stats'),

    # Функциональные представления
    path('<int:pk>/logs/', views.mailing_logs, name='mailing_logs'),
    path('<int:pk>/stats-detailed/', views.mailing_stats_detailed, name='mailing_stats_detailed'),

    # Классовые представления
    path('<int:pk>/statistics/', MailingStatisticsView.as_view(), name='mailing_statistics_class'),
    path('<int:pk>/logs-class/', MailingLogsView.as_view(), name='mailing_logs_class'),
    path('overall-statistics/', OverallStatisticsView.as_view(), name='overall_statistics'),

    # Алиасы для удобства
    path('<int:pk>/statistics/new/', MailingStatisticsView.as_view(), name='mailing_statistics_new'),
    path('<int:pk>/logs/new/', MailingLogsView.as_view(), name='mailing_logs_new'),
]
