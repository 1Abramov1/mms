from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Кастомная админка для модели пользователя
    """
    # Отображение в списке
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'email_verified', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('email_verified', 'is_staff', 'is_active', 'is_superuser',
                   'date_joined', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login')

    # Поля в форме редактирования
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Email verification'), {'fields': ('email_verified', 'verification_token',
                                              'token_created_at')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                       'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Поля в форме создания пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2',
                       'is_staff', 'is_active', 'email_verified'),
        }),
    )

    # Действия в админке
    actions = ['verify_email', 'unverify_email']

    def verify_email(self, request, queryset):
        """Действие: подтвердить email"""
        updated = queryset.update(email_verified=True)
        self.message_user(request, f'Подтверждено {updated} email(ов).')

    verify_email.short_description = "Подтвердить выбранные email"

    def unverify_email(self, request, queryset):
        """Действие: снять подтверждение email"""
        updated = queryset.update(email_verified=False)
        self.message_user(request, f'Снято подтверждение с {updated} email(ов).')

    unverify_email.short_description = "Снять подтверждение email"

    # Метод для отображения статуса email в списке
    @admin.display(boolean=True, description='Email подтвержден')
    def email_verified_status(self, obj):
        return obj.email_verified