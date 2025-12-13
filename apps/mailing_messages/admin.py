from django.contrib import admin
from django.utils.html import format_html
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели Message
    """
    list_display = ('subject', 'short_body_display', 'created_at', 'created_by', 'admin_actions')
    list_filter = ('created_at', 'created_by')
    search_fields = ('subject', 'body')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    fieldsets = (
        ('Основная информация', {
            'fields': ('subject', 'body')
        }),
        ('Дополнительная информация', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def short_body_display(self, obj):
        """Сокращенное тело письма для отображения в списке"""
        return obj.short_body()

    short_body_display.short_description = 'Тело письма'

    def admin_actions(self, obj):
        """Кнопки действий в админке"""
        return format_html(
            '<a href="/admin/mailing_messages/message/{}/change/" style="margin-right: 10px;">✏️</a> '
            '<a href="/admin/mailing_messages/message/{}/delete/">🗑️</a>',
            obj.id, obj.id
        )

    admin_actions.short_description = 'Действия'

    def save_model(self, request, obj, form, change):
        """Автоматически устанавливаем создателя сообщения"""
        if not obj.pk:  # Если объект создается впервые
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
