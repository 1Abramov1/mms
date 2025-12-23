from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import hashlib
import uuid


class User(AbstractUser):
    """
    Кастомная модель пользователя с подтверждением email
    Согласно ТЗ пункт 7: Регистрация и аутентификация пользователей
    """
    # Поле для подтверждения email (ТЗ: подтвердив свой email)
    email_verified = models.BooleanField(
        default=False,
        verbose_name='Email подтвержден'
    )

    # Токен для подтверждения email
    verification_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Токен подтверждения'
    )

    # Время создания токена
    token_created_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Время создания токена'
    )

    # Токен для сброса пароля (ТЗ: восстановление пароля)
    password_reset_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Токен сброса пароля'
    )

    # Время создания токена сброса пароля
    password_reset_token_created = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Время создания токена сброса'
    )

    # Для избежания конфликтов с related_name
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='Группы',
        blank=True,
        help_text='Группы, к которым принадлежит пользователь.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='Права доступа',
        blank=True,
        help_text='Конкретные права доступа для этого пользователя.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']
        db_table = 'users_user'

    def __str__(self):
        """Строковое представление пользователя"""
        return f'{self.username} ({self.email})'

    def send_verification_email(self, request):
        """
        Отправка письма для подтверждения email
        ТЗ: Пользователи должны иметь возможность зарегистрироваться на сайте, подтвердив свой email
        """
        # Генерируем уникальный токен
        token = uuid.uuid4().hex
        self.verification_token = hashlib.sha256(token.encode()).hexdigest()
        self.token_created_at = timezone.now()
        self.save()

        # Формируем полный URL для подтверждения
        if hasattr(settings, 'SITE_URL'):
            base_url = settings.SITE_URL
        else:
            base_url = f"http://{request.get_host()}"

        verification_url = f"{base_url}/users/verify-email/{token}/"

        # Отправляем email (ТЗ: подтверждение email)
        send_mail(
            subject='Подтверждение email адреса - MMS Рассылки',
            message=f'Здравствуйте, {self.username}!\n\n'
                   f'Для подтверждения вашего email адреса перейдите по ссылке:\n'
                   f'{verification_url}\n\n'
                   f'Если вы не регистрировались в системе MMS, проигнорируйте это письмо.\n\n'
                   f'С уважением,\nКоманда MMS Рассылок',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            fail_silently=False,
        )
        return token

    def send_password_reset_email(self, request):
        """
        Отправка письма для сброса пароля
        ТЗ: Необходимо предусмотреть возможность восстановления пароля
        """
        # Генерируем уникальный токен для сброса пароля
        token = uuid.uuid4().hex
        self.password_reset_token = hashlib.sha256(token.encode()).hexdigest()
        self.password_reset_token_created = timezone.now()
        self.save()

        # Формируем полный URL для сброса пароля
        if hasattr(settings, 'SITE_URL'):
            base_url = settings.SITE_URL
        else:
            base_url = f"http://{request.get_host()}"

        reset_url = f"{base_url}/users/password-reset/{token}/"

        # Отправляем email для сброса пароля
        send_mail(
            subject='Сброс пароля - MMS Рассылки',
            message=f'Здравствуйте, {self.username}!\n\n'
                    f'Для сброса пароля перейдите по ссылке:\n'
                    f'{reset_url}\n\n'
                    f'Если вы не запрашивали сброс пароля, проигнорируйте это письмо.\n'
                    f'Ссылка действительна в течение 24 часов.\n\n'
                    f'С уважением,\nКоманда MMS Рассылок',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            fail_silently=False,
        )
        return token

    def is_verification_token_valid(self, max_age_hours=24):
        """
        Проверяет валидность токена подтверждения email
        """
        if not self.verification_token or not self.token_created_at:
            return False

        # Проверяем срок действия токена
        time_diff = timezone.now() - self.token_created_at
        return time_diff.total_seconds() <= max_age_hours * 3600

    def is_password_reset_token_valid(self, max_age_hours=24):
        """
        Проверяет валидность токена сброса пароля
        """
        if not self.password_reset_token or not self.password_reset_token_created:
            return False

        # Проверяем срок действия токена
        time_diff = timezone.now() - self.password_reset_token_created
        return time_diff.total_seconds() <= max_age_hours * 3600

    def clear_verification_token(self):
        """Очищает токен подтверждения email"""
        self.verification_token = None
        self.token_created_at = None
        self.save()

    def clear_password_reset_token(self):
        """Очищает токен сброса пароля"""
        self.password_reset_token = None
        self.password_reset_token_created = None
        self.save()

    @property
    def can_login(self):
        """
        Проверяет, может ли пользователь войти в систему
        ТЗ: функция входа в систему (только с подтвержденным email)
        """
        return self.email_verified and self.is_active

    # Методы для админки (для красивого отображения)
    @property
    def display_name(self):
        """Отображаемое имя пользователя"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    @property
    def registration_date(self):
        """Дата регистрации в удобном формате"""
        return self.date_joined.strftime("%d.%m.%Y %H:%M") if self.date_joined else "Не указано"

    @property
    def last_login_date(self):
        """Дата последнего входа в удобном формате"""
        return self.last_login.strftime("%d.%m.%Y %H:%M") if self.last_login else "Никогда"