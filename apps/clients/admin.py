from django.contrib import admin
from django.utils.html import format_html
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели Client
    """
    list_display = ('email', 'full_name', 'short_comment', 'created_at', 'admin_actions')
    list_filter = ('created_at',)
    search_fields = ('email', 'full_name', 'comment')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('email', 'full_name')
        }),
        ('Дополнительная информация', {
            'fields': ('comment',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def short_comment(self, obj):
        """Сокращенный комментарий для отображения в списке"""
        if obj.comment:
            return obj.comment[:50] + ('...' if len(obj.comment) > 50 else '')
        return '-'

    short_comment.short_description = 'Комментарий'

    def admin_actions(self, obj):
        """Кнопки действий в админке"""
        return format_html(
            '<a href="/admin/clients/client/{}/change/" style="margin-right: 10px;">✏️</a> '
            '<a href="/admin/clients/client/{}/delete/">🗑️</a>',
            obj.id, obj.id
        )

    admin_actions.short_description = 'Действия'