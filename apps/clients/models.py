from django.db import models
from django.core.validators import EmailValidator


class Client(models.Model):
    """
    Модель Получатель рассылки (клиент)
    """
    email = models.EmailField(
        verbose_name='Email',
        max_length=255,
        unique=True,
        validators=[EmailValidator()],
        help_text='Введите действительный email адрес'
    )

    full_name = models.CharField(
        verbose_name='Ф. И. О.',
        max_length=200,
        help_text='Введите полное имя клиента'
    )

    comment = models.TextField(
        verbose_name='Комментарий',
        blank=True,
        null=True,
        help_text='Дополнительная информация о клиенте'
    )

    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        verbose_name='Дата обновления',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.email})"
