import logging
import smtplib
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from .models import MailingLog, Mailing

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
        Основной метод отправки рассылки с созданием логов согласно ТЗ 5
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

                    # СОЗДАНИЕ ЛОГА ПО ТЗ 5:
                    MailingLog.objects.create(
                        mailing=mailing,
                        status=MailingLog.STATUS_SUCCESS,
                        server_response="Сообщение успешно отправлено (режим разработки)",
                        client_email=client.email,
                        message_subject=subject[:255] if subject else 'Без темы'
                    )
                    successful_sends += 1

                else:
                    # Реальная отправка
                    result = send_mail(
                        subject=subject,
                        message=message_body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[recipient_email],
                        fail_silently=False,
                    )

                    # СОЗДАНИЕ ЛОГА ПО ТЗ 5:
                    MailingLog.objects.create(
                        mailing=mailing,
                        status=MailingLog.STATUS_SUCCESS,
                        server_response=f"Успешно отправлено на {client.email}. Сообщений отправлено: {result}",
                        client_email=client.email,
                        message_subject=subject[:255] if subject else 'Без темы'
                    )
                    successful_sends += 1

            except smtplib.SMTPException as e:
                # Ошибка SMTP сервера
                MailingLog.objects.create(
                    mailing=mailing,
                    status=MailingLog.STATUS_FAILED,
                    server_response=f"SMTP ошибка: {str(e)}. Код: {e.smtp_code if hasattr(e, 'smtp_code') else 'N/A'}",
                    client_email=client.email,
                    message_subject=subject[:255] if subject else 'Без темы'
                )
                failed_sends += 1
                logger.error(f"SMTP ошибка отправки клиенту {client.email}: {e}")

            except Exception as e:
                # Общая ошибка
                MailingLog.objects.create(
                    mailing=mailing,
                    status=MailingLog.STATUS_FAILED,
                    server_response=f"Ошибка: {type(e).__name__}: {str(e)}",
                    client_email=client.email,
                    message_subject=subject[:255] if subject else 'Без темы'
                )
                failed_sends += 1
                logger.error(f"Общая ошибка отправки клиенту {client.email}: {e}")

        # 4. Обновляем статус рассылки
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
            'last_sent': logs.order_by('-attempt_time').first(),
            'first_sent': logs.order_by('attempt_time').first(),
        }

        if stats['total'] > 0:
            stats['success_rate'] = (stats['success'] / stats['total']) * 100
        else:
            stats['success_rate'] = 0

        return stats

    # ДОБАВЛЕНО ПО ТЗ 5: Новые методы для работы с логами

    @staticmethod
    def get_mailing_statistics(mailing):
        """
        Полная статистика по рассылке согласно ТЗ
        """
        logs = mailing.logs.all()
        total = logs.count()
        successful = logs.filter(status=MailingLog.STATUS_SUCCESS).count()
        failed = logs.filter(status=MailingLog.STATUS_FAILED).count()

        return {
            'total_attempts': total,
            'successful_attempts': successful,
            'failed_attempts': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'last_attempt': logs.order_by('-attempt_time').first(),
            'first_attempt': logs.order_by('attempt_time').first(),
        }

    @staticmethod
    def get_detailed_logs(mailing, limit=50):
        """
        Детальные логи с возможностью диагностики
        """
        return mailing.logs.all().order_by('-attempt_time')[:limit]

    @staticmethod
    def get_hourly_statistics(mailing, hours=24):
        """
        Статистика по часам за последние N часов
        """
        since = timezone.now() - timedelta(hours=hours)

        # Для SQLite (простая реализация)
        if 'sqlite' in settings.DATABASES['default']['ENGINE']:
            logs = mailing.logs.filter(attempt_time__gte=since)
            stats = {}
            for log in logs:
                hour = log.attempt_time.strftime('%H:00')
                if hour not in stats:
                    stats[hour] = {'success': 0, 'failed': 0}

                if log.status == MailingLog.STATUS_SUCCESS:stats[hour]['success'] += 1

                else:
                    stats[hour]['failed'] += 1

                result = []
                for hour, counts in sorted(stats.items()):
                    result.append({
                        'hour': hour,
                        'success_count': counts['success'],
                        'failed_count': counts['failed'],
                        'total': counts['success'] + counts['failed']
                    })
                return result
            else:
                # Для PostgreSQL/MySQL
                return mailing.logs.filter(
                    attempt_time__gte=since
                ).extra({
                    'hour': "EXTRACT(HOUR FROM attempt_time AT TIME ZONE 'UTC')"
                }).values('hour', 'status').annotate(
                    count=Count('id')
                ).order_by('hour', 'status')

    @staticmethod
    def get_client_delivery_history(client_email, limit=20):
        """
        История доставки для конкретного клиента
        """
        return MailingLog.objects.filter(
            client_email=client_email
        ).select_related('mailing').order_by('-attempt_time')[:limit]

    @staticmethod
    def check_and_process_active_mailings():
        """
        Проверяет и обрабатывает все активные рассылки
        """
        now = timezone.now()
        active_mailings = Mailing.objects.filter(
            start_time__lte=now,
            end_time__gte=now,
            status__in=[Mailing.STATUS_CREATED, Mailing.STATUS_STARTED]
        )

        results = []
        for mailing in active_mailings:
            success, message = MailingService.send_mailing(mailing)
            results.append({
                'mailing_id': mailing.id,
                'subject': mailing.message.subject if mailing.message else 'N/A',
                'success': success,
                'message': message
            })

        logger.info(f"Обработано активных рассылок: {len(results)}")
        return results

    @staticmethod
    def get_overall_statistics():
        """
        Общая статистика по всем рассылкам
        """
        total_mailings = Mailing.objects.count()
        total_logs = MailingLog.objects.count()
        successful_logs = MailingLog.objects.filter(status=MailingLog.STATUS_SUCCESS).count()

        return {
            'total_mailings': total_mailings,
            'total_logs': total_logs,
            'successful_logs': successful_logs,
            'failed_logs': total_logs - successful_logs,
            'success_rate': (successful_logs / total_logs * 100) if total_logs > 0 else 0,
            'unique_clients': MailingLog.objects.values('client_email').distinct().count(),
        }
