import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import MailingLog


logger = logging.getLogger(__name__)


class MailingService:
    """
    Сервис для отправки рассылок
    """

    @staticmethod
    def validate_mailing_time(mailing):
        """
        Проверка времени рассылки согласно ТЗ
        """
        now = timezone.now()

        if mailing.start_time <= now <= mailing.end_time:
            return True, None
        elif now < mailing.start_time:
            return False, f"Рассылка еще не началась. Начнется в {mailing.start_time.strftime('%d.%m.%Y %H:%M')}"
        else:
            return False, f"Рассылка уже завершилась. Завершилась в {mailing.end_time.strftime('%d.%m.%Y %H:%M')}"

    @staticmethod
    def send_mailing(mailing):
        """
        Основной метод отправки рассылки
        """
        # 1. Проверка времени
        is_valid, error_message = MailingService.validate_mailing_time(mailing)
        if not is_valid:
            logger.error(f"Рассылка {mailing.id}: {error_message}")
            return False, error_message

        # 2. Определение получателей
        recipients = mailing.recipients.all()
        if not recipients.exists():
            error_msg = "Нет получателей для рассылки"
            logger.error(f"Рассылка {mailing.id}: {error_msg}")
            return False, error_msg

        # 3. Отправка писем каждому клиенту
        successful_sends = 0
        failed_sends = 0

        for client in recipients:
            try:
                subject = mailing.message.subject
                message_body = mailing.message.body
                recipient_email = client.email

                # Для теста используем консольный вывод
                if settings.DEBUG:
                    print(f"[EMAIL DEBUG] Отправка клиенту {client.email}:")
                    print(f"Тема: {subject}")
                    print(f"Тело: {message_body[:100]}...")

                    # Создаем успешный лог для теста
                    MailingLog.objects.create(
                        mailing=mailing,
                        client=client,
                        status=MailingLog.STATUS_SUCCESS,
                        server_response="Сообщение успешно отправлено (режим разработки)"
                    )
                    successful_sends += 1

                else:
                    # Реальная отправка
                    send_mail(
                        subject=subject,
                        message=message_body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[recipient_email],
                        fail_silently=False,
                    )

                    MailingLog.objects.create(
                        mailing=mailing,
                        client=client,
                        status=MailingLog.STATUS_SUCCESS
                    )
                    successful_sends += 1

            except Exception as e:
                # Создаем лог с ошибкой
                MailingLog.objects.create(
                    mailing=mailing,
                    client=client,
                    status=MailingLog.STATUS_FAILED,
                    error_message=str(e)
                )
                failed_sends += 1
                logger.error(f"Ошибка отправки клиенту {client.email}: {e}")

        # 4. Обновляем статус рассылки (ВНЕ цикла for!)
        mailing.update_status()
        result_message = f"Отправлено успешно: {successful_sends}, с ошибками: {failed_sends}"
        logger.info(f"Рассылка {mailing.id}: {result_message}")

        return True, result_message

    @staticmethod
    def send_test_email(client_email, subject, message):
        """
        Метод для тестовой отправки email
        """
        try:
            if settings.DEBUG:
                print(f"[TEST EMAIL] Отправка на {client_email}:")
                print(f"Тема: {subject}")
                print(f"Тело: {message}")
                return True, "Тестовое письмо отправлено (режим разработки)"
            else:
                # Реальная отправка в продакшене
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[client_email],
                    fail_silently=False,
                )
                return True, "Тестовое письмо отправлено"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_mailing_stats(mailing):
        """
        Получение статистики по рассылке
        """
        logs = mailing.logs.all()

        stats = {
            'total': logs.count(),
            'success': logs.filter(status=MailingLog.STATUS_SUCCESS).count(),
            'failed': logs.filter(status=MailingLog.STATUS_FAILED).count(),
            'last_sent': logs.order_by('-sent_at').first(),
        }

        if stats['total'] > 0:
            stats['success_rate'] = (stats['success'] / stats['total']) * 100
        else:
            stats['success_rate'] = 0

        return stats