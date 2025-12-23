from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Регистрация и вход/выход
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Подтверждение email
    path('verify-email/<str:token>/', views.verify_email_view, name='verify_email'),
    path('resend-verification/', views.resend_verification_view, name='resend_verification'),

    # Сброс пароля
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/<str:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),

    # Профиль
    path('profile/', views.profile_view, name='profile'),
    path('profile/delete/', views.profile_delete_view, name='profile_delete'),
]