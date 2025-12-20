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
        editable=False
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
        """Строковое представление рассылки"""
        if self.start_time:
            start_time_str = self.start_time.strftime('%d.%m.%Y %H:%M')
        else:
            start_time_str = 'Не указано'
        return f"Рассылка от {start_time_str} - {self.get_status_display()}"

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
                    self.__class__.objects.filter(pk=self.pk).update(status=new_status)

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
        if self.calculate_status() == self.STATUS_CREATED and self.start_time:
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


class MailingLog(models.Model):
    """
    Лог отправки сообщения (Попытка рассылки)
    Соответствует ТЗ пункт 5:
    - Дата и время попытки (attempt_time)
    - Статус ('Успешно', 'Не успешно')
    - Ответ почтового сервера (server_response)
    - Рассылка (mailing, внешний ключ на модель «Рассылка»)
    """

    STATUS_SUCCESS = 'Успешно'
    STATUS_FAILED = 'Не успешно'
    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Успешно'),
        (STATUS_FAILED, 'Не успешно'),
    ]

    # внешний ключ на рассылку
    mailing = models.ForeignKey(
        Mailing,
        verbose_name='Рассылка',
        on_delete=models.CASCADE,
        related_name='logs'
    )

    # связь с клиентом
    client = models.ForeignKey(
        'clients.Client',
        verbose_name='Клиент',
        on_delete=models.CASCADE,
        related_name='mailing_logs',
        null=True,  # временно null=True для обратной совместимости
        blank=True
    )

    # статус попытки
    status = models.CharField(
        verbose_name='Статус',
        max_length=20,
        choices=STATUS_CHOICES
    )

    # ответ почтового сервера
    server_response = models.TextField(
        verbose_name='Ответ почтового сервера',
        blank=True,
        null=True,
        help_text='Ответ SMTP сервера при отправке письма'
    )

    # дата и время попытки
    attempt_time = models.DateTimeField(
        verbose_name='Дата и время попытки',
        default=timezone.now,
        help_text='Время создания записи о попытке отправки'
    )

    # Для обратной совместимости оставляем sent_at
    sent_at = models.DateTimeField(
        verbose_name='Дата и время отправки',
        auto_now_add=True,
        editable=False
    )

    # Сообщения об ошибке
    error_message = models.TextField(
        verbose_name='Сообщение об ошибке',
        blank=True,
        null=True,
        help_text='Подробное сообщение об ошибке'
    )

    # ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ (не в ТЗ):
    client_email = models.EmailField(
        verbose_name='Email получателя',
        blank=True,
        null=True,
        help_text='Email адрес, на который отправлялось письмо'
    )

    message_subject = models.CharField(
        verbose_name='Тема письма',
        max_length=255,
        blank=True,
        null=True,
        help_text='Тема отправленного письма'
    )

    class Meta:
        verbose_name = 'Попытка рассылки'
        verbose_name_plural = 'Попытки рассылок'
        ordering = ['-attempt_time']  # Используем attempt_time согласно ТЗ
        indexes = [
            models.Index(fields=['attempt_time']),
            models.Index(fields=['status']),
            models.Index(fields=['mailing']),
            models.Index(fields=['client']),
            models.Index(fields=['client_email']),
        ]

    def save(self, *args, **kwargs):
        """Синхронизация sent_at и attempt_time для обратной совместимости"""
        if not self.attempt_time:
            self.attempt_time = timezone.now()
        self.sent_at = self.attempt_time  # Для старых записей

        # Если есть клиент, заполняем его email
        if self.client and not self.client_email:
            self.client_email = self.client.email

        super().save(*args, **kwargs)

    def __str__(self):
        """Строковое представление согласно ТЗ"""
        mailing_id = self.mailing_id if hasattr(self, 'mailing_id') else 'Нет рассылки'
        time_str = self.attempt_time.strftime('%d.%m.%Y %H:%M') if self.attempt_time else 'Нет времени'
        email = self.client_email or (self.client.email if self.client else 'Нет email')
        return f"Попытка {mailing_id} - {email} - {self.status} - {time_str}"

    def is_successful(self):
        """Проверяет успешность попытки"""
        return self.status == self.STATUS_SUCCESS

    def get_short_response(self):
        """Короткая версия ответа сервера (для отображения в списках)"""
        if self.server_response:
            return (self.server_response[:100] + '...'
                    if len(self.server_response) > 100
                    else self.server_response)
        return 'Нет ответа сервера'
