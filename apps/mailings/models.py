from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from apps.mailing_messages.models import Message
from apps.clients.models import Client
from typing import Optional, TYPE_CHECKING
from datetime import datetime as dt
import datetime

if TYPE_CHECKING:
    from django.db.models.manager import Manager
    from apps.clients.models import Client as ClientType


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
    start_time: 'models.DateTimeField' = models.DateTimeField(
        verbose_name='Дата и время начала отправки',
        help_text='С какого момента рассылка может быть запущена'
    )

    end_time: 'models.DateTimeField' = models.DateTimeField(
        verbose_name='Дата и время окончания отправки',
        help_text='До какого момента разрешено выполнять отправку'
    )

    status: 'models.CharField' = models.CharField(
        verbose_name='Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        editable=False  # Статус вычисляется динамически
    )

    message: 'models.ForeignKey' = models.ForeignKey(
        Message,
        verbose_name='Сообщение',
        on_delete=models.CASCADE,
        related_name='mailings'
    )

    recipients: 'models.ManyToManyField' = models.ManyToManyField(
        Client,
        verbose_name='Получатели',
        related_name='mailings'
    )

    # Дополнительные поля
    created_at: 'models.DateTimeField' = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )

    updated_at: 'models.DateTimeField' = models.DateTimeField(
        verbose_name='Дата обновления',
        auto_now=True
    )

    created_by: 'models.ForeignKey' = models.ForeignKey(
        User,
        verbose_name='Создал',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_mailings'
    )

    # Аннотации для менеджеров
    if TYPE_CHECKING:
        objects: Manager['Mailing']

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

    def __str__(self) -> str:
        """Строковое представление рассылки"""
        start_time_value: Optional[dt] = self.start_time

        if start_time_value:
            start_time_str = start_time_value.strftime('%d.%m.%Y %H:%M')
        else:
            start_time_str = 'Не указано'

        status_display = self.get_status_display() if hasattr(self, 'get_status_display') else 'Неизвестно'
        return f"Рассылка от {start_time_str} - {status_display}"

    def clean(self) -> None:
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

    def calculate_status(self) -> str:
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

    def update_status(self, save: bool = True) -> str:
        """
        Обновляет статус рассылки в базе данных
        Если save=True - сохраняет изменения в БД
        """
        new_status = self.calculate_status()

        if self.status != new_status:
            self.status = new_status
            if save:
                # Используем self.__class__ вместо явного указания Mailing
                self.__class__.objects.filter(pk=self.pk).update(status=new_status)

        return self.status

    def get_absolute_url(self) -> str:
        from django.urls import reverse
        return reverse('mailings:mailing_detail', kwargs={'pk': self.pk})

    def recipients_count(self) -> int:
        """Количество получателей"""
        if TYPE_CHECKING:
            return self.recipients.count()  # type: ignore
        return self.recipients.count()

    recipients_count.short_description = 'Кол-во получателей'

    def is_active(self) -> bool:
        """Проверяет, активна ли рассылка в данный момент"""
        return self.calculate_status() == self.STATUS_STARTED

    def time_until_start(self) -> Optional[str]:
        """Время до начала рассылки (для созданных)"""
        if self.calculate_status() == self.STATUS_CREATED:
            # Проверяем, что start_time существует
            if self.start_time:
                # Приводим к datetime для операции вычитания
                start_time_dt: dt = self.start_time
                delta: datetime.timedelta = start_time_dt - timezone.now()
                days = delta.days
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                return f"{days}д {hours}ч {minutes}м"
        return None

    def duration(self) -> Optional[str]:
        """Длительность рассылки"""
        if self.end_time and self.start_time:
            # Приводим к datetime для операции вычитания
            end_time_dt: dt = self.end_time
            start_time_dt: dt = self.start_time
            delta: datetime.timedelta = end_time_dt - start_time_dt
            days = delta.days
            hours = delta.seconds // 3600
            return f"{days}д {hours}ч"
        return None

class MailingLog(models.Model):
    """
    Лог отправки сообщения
    """
    STATUS_SUCCESS = 'Успешно'
    STATUS_FAILED = 'Не успешно'
    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Успешно'),
        (STATUS_FAILED, 'Не успешно'),
    ]

    mailing: 'models.ForeignKey' = models.ForeignKey(
        Mailing,
        verbose_name='Рассылка',
        on_delete=models.CASCADE,
        related_name='logs'
    )

    client: 'models.ForeignKey' = models.ForeignKey(
        Client,
        verbose_name='Клиент',
        on_delete=models.CASCADE,
        related_name='mailing_logs'
    )

    status: 'models.CharField' = models.CharField(
        verbose_name='Статус',
        max_length=20,
        choices=STATUS_CHOICES
    )

    error_message: 'models.TextField' = models.TextField(
        verbose_name='Сообщение об ошибке',
        blank=True,
        null=True
    )

    sent_at: 'models.DateTimeField' = models.DateTimeField(
        verbose_name='Дата и время отправки',
        auto_now_add=True
    )

    server_response: 'models.TextField' = models.TextField(
        verbose_name='Ответ сервера',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Лог отправки'
        verbose_name_plural = 'Логи отправки'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['sent_at']),
            models.Index(fields=['status']),
            models.Index(fields=['mailing']),
        ]

    def __str__(self) -> str:
        """Строковое представление лога"""
        # Используем id напрямую из ForeignKey
        mailing_id = self.mailing_id if hasattr(self, 'mailing_id') else 'Нет рассылки'

        # Проверяем, что клиент существует
        client_obj: Optional['ClientType'] = self.client
        if client_obj and hasattr(client_obj, 'email'):
            client_email = client_obj.email
        else:
            client_email = 'Нет клиента'

        return f"Лог {mailing_id} - {client_email} - {self.status}"

    def is_successful(self) -> bool:
        return self.status == self.STATUS_SUCCESS
