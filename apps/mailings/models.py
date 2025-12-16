from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from apps.mailing_messages.models import Message
from apps.clients.models import Client


class Mailing(models.Model):
    """
    Модель Рассылка - связывает сообщения и клиентов
    """

    # Статусы рассылки
    STATUS_CREATED = 'Создана'
    STATUS_STARTED = 'Запущена'
    STATUS_COMPLETED = 'Завершена'
    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создана'),
        (STATUS_STARTED, 'Запущена'),
        (STATUS_COMPLETED, 'Завершена'),
    ]

    # Поля из ТЗ
    start_time = models.DateTimeField(
        verbose_name='Дата и время начала отправки',
        help_text='С какого момента рассылка может быть запущена'
    )

    end_time = models.DateTimeField(
        verbose_name='Дата и время окончания отправки',
        help_text='До какого момента разрешено выполнять отправку'
    )

    status = models.CharField(
        verbose_name='Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        editable=False  # Статус вычисляется динамически
    )

    message = models.ForeignKey(
        Message,
        verbose_name='Сообщение',
        on_delete=models.CASCADE,
        related_name='mailings'
    )

    recipients = models.ManyToManyField(
        Client,
        verbose_name='Получатели',
        related_name='mailings'
    )

    # Дополнительные поля
    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        verbose_name='Дата обновления',
        auto_now=True
    )

    created_by = models.ForeignKey(
        User,
        verbose_name='Создал',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_mailings'
    )

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['start_time']),
            models.Index(fields=['end_time']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Рассылка от {self.start_time.strftime('%d.%m.%Y %H:%M')} - {self.get_status_display()}"

    def clean(self):
        """Валидация модели перед сохранением"""
        super().clean()

        # Валидация 1: start_time не может быть в прошлом
        if self.start_time and self.start_time < timezone.now():
            raise ValidationError({
                'start_time': 'Дата начала не может быть в прошлом'
            })

        # Валидация 2: start_time должен быть раньше end_time
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({
                'start_time': 'Дата начала должна быть раньше даты окончания',
                'end_time': 'Дата окончания должна быть позже даты начала'
            })

    def calculate_status(self):
        """
        Динамически вычисляет статус рассылки на основе текущего времени
        Согласно ТЗ:
        - 'Создана' - текущая дата раньше start_time
        - 'Запущена' - текущая дата между start_time и end_time (включительно)
        - 'Завершена' - текущая дата позже end_time
        """
        now = timezone.now()

        if now < self.start_time:
            return self.STATUS_CREATED
        elif self.start_time <= now <= self.end_time:
            return self.STATUS_STARTED
        else:
            return self.STATUS_COMPLETED

    def update_status(self, save=True):
        """
        Обновляет статус рассылки в базе данных
        Если save=True - сохраняет изменения в БД
        """
        new_status = self.calculate_status()

        if self.status != new_status:
            self.status = new_status
            if save:
                # Сохраняем только поле status, чтобы не трогать updated_at
                Mailing.objects.filter(pk=self.pk).update(status=new_status)

        return self.status

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('mailings:mailing_detail', kwargs={'pk': self.pk})

    def recipients_count(self):
        """Количество получателей"""
        return self.recipients.count()

    recipients_count.short_description = 'Кол-во получателей'

    def is_active(self):
        """Проверяет, активна ли рассылка в данный момент"""
        return self.calculate_status() == self.STATUS_STARTED

    def time_until_start(self):
        """Время до начала рассылки (для созданных)"""
        if self.calculate_status() == self.STATUS_CREATED:
            delta = self.start_time - timezone.now()
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            return f"{days}д {hours}ч {minutes}м"
        return None

    def duration(self):
        """Длительность рассылки"""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            days = delta.days
            hours = delta.seconds // 3600
            return f"{days}д {hours}ч"
        return None
