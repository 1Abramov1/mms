from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Mailing


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели Mailing
    """
    list_display = (
        'id',
        'start_time_display',
        'end_time_display',
        'status_display',
        'message_subject',
        'recipients_count_display',
        'created_by_display',
        'admin_actions'
    )

    list_filter = ('status', 'start_time', 'created_by')
    search_fields = ('message__subject', 'recipients__email', 'recipients__full_name')
    ordering = ('-start_time',)

    readonly_fields = (
        'status',
        'created_at',
        'updated_at',
        'created_by',
        'recipients_count_display',
        'duration_display',
        'time_until_start_display'
    )

    fieldsets = (
        ('Основная информация', {
            'fields': ('start_time', 'end_time', 'message', 'recipients')
        }),
        ('Статус и информация', {
            'fields': (
                'status',
                'recipients_count_display',
                'duration_display',
                'time_until_start_display'
            ),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    filter_horizontal = ('recipients',)  # Удобный виджет для ManyToMany

    def start_time_display(self, obj):
        """Отображение start_time в списке"""
        return obj.start_time.strftime('%d.%m.%Y %H:%M')

    start_time_display.short_description = 'Начало'
    start_time_display.admin_order_field = 'start_time'

    def end_time_display(self, obj):
        """Отображение end_time в списке"""
        return obj.end_time.strftime('%d.%m.%Y %H:%M')

    end_time_display.short_description = 'Окончание'
    end_time_display.admin_order_field = 'end_time'

    def status_display(self, obj):
        """Цветное отображение статуса"""
        obj.update_status()  # Обновляем статус перед отображением

        colors = {
            'Создана': 'info',
            'Запущена': 'success',
            'Завершена': 'secondary'
        }

        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )

    status_display.short_description = 'Статус'

    def message_subject(self, obj):
        """Отображение темы сообщения"""
        if obj.message and len(obj.message.subject) > 30:
            return obj.message.subject[:30] + '...'
        return obj.message.subject if obj.message else '-'

    message_subject.short_description = 'Сообщение'

    def recipients_count_display(self, obj):
        """Отображение количества получателей"""
        return obj.recipients_count()

    recipients_count_display.short_description = 'Получателей'

    def created_by_display(self, obj):
        """Отображение создателя"""
        return obj.created_by.username if obj.created_by else '-'

    created_by_display.short_description = 'Создал'

    def duration_display(self, obj):
        """Отображение длительности рассылки"""
        duration = obj.duration()
        return duration if duration else '-'

    duration_display.short_description = 'Длительность'

    def time_until_start_display(self, obj):
        """Отображение времени до начала"""
        time_until = obj.time_until_start()
        if time_until:
            return format_html('<span class="text-info">Начнется через: {}</span>', time_until)
        return '-'

    time_until_start_display.short_description = 'До начала'

    def admin_actions(self, obj):
        """Кнопки действий в админке"""
        return format_html(
            '<a href="/admin/mailings/mailing/{}/change/" style="margin-right: 10px;">✏️</a> '
            '<a href="/admin/mailings/mailing/{}/delete/">🗑️</a>',
            obj.id, obj.id
        )

    admin_actions.short_description = 'Действия'

    def save_model(self, request, obj, form, change):
        """Автоматически устанавливаем создателя"""
        if not obj.pk:  # Если объект создается впервые
            obj.created_by = request.user

        # Обновляем статус перед сохранением
        obj.update_status(save=False)

        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Обновляем статус всех рассылок в queryset"""
        qs = super().get_queryset(request)

        # Обновляем статус для каждой рассылки
        for mailing in qs:
            mailing.update_status()

        return qs