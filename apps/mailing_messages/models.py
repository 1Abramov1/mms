from django.db import models
from django.conf import settings


class Message(models.Model):
    """
    Модель Сообщение для рассылки
    """
    subject = models.CharField(
        verbose_name='Тема письма',
        max_length=255,
        help_text='Введите тему письма'
    )

    body = models.TextField(
        verbose_name='Тело письма',
        help_text='Введите текст сообщения'
    )

    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        verbose_name='Дата обновления',
        auto_now=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Создал',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_messages'
    )

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subject']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.subject

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('mailing_messages:message_detail', kwargs={'pk': self.pk})

    def short_body(self):
        """Сокращенное тело сообщения для отображения в списке"""
        if len(self.body) > 100:
            return self.body[:100] + '...'
        return self.body

    short_body.short_description = 'Тело письма (кратко)'
