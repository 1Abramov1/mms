from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core import mail
from django.apps import apps
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Ручной запуск рассылки через командную строку'

    def add_arguments(self, parser):
        parser.add_argument('mailing_id', type=int, help='ID рассылки для запуска')

    def handle(self, *args, **options):
        mailing_id = options['mailing_id']
        current_time = timezone.now()

        try:
            # Получаем модели
            Mailing = apps.get_model('mailings', 'Mailing')
            MailingLog = apps.get_model('mailings', 'MailingLog')

            # Находим рассылку
            mailing = Mailing.objects.get(id=mailing_id)

            # Проверяем время
            if current_time < mailing.start_time:
                self.stdout.write(self.style.ERROR(f'Рассылка еще не началась'))
                return

            if current_time > mailing.end_time:
                self.stdout.write(self.style.ERROR(f'Рассылка уже завершена'))
                return

            # Начинаем отправку
            self.stdout.write(self.style.SUCCESS(f'Запуск рассылки: {mailing.message.subject}'))

            clients = mailing.recipients.all()
            total_clients = clients.count()
            self.stdout.write(f'Найдено получателей: {total_clients}')

            success = 0
            failed = 0

            # Отправляем каждому клиенту
            for client in clients:
                try:
                    self.stdout.write(f'Отправка {client.email}...', ending=' ')

                    # Отправка email
                    mail.send_mail(
                        subject=mailing.message.subject,
                        message=mailing.message.body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[client.email],
                        fail_silently=False,
                    )

                    # Лог успеха
                    MailingLog.objects.create(
                        mailing=mailing,
                        client=client,
                        status='Успешно',
                        server_response='OK',
                        client_email=client.email,
                        message_subject=mailing.message.subject
                    )

                    success += 1
                    self.stdout.write(self.style.SUCCESS('OK'))

                except Exception as e:
                    # Лог ошибки
                    MailingLog.objects.create(
                        mailing=mailing,
                        client=client,
                        status='Не успешно',
                        server_response=str(e),
                        error_message=str(e),
                        client_email=client.email,
                        message_subject=mailing.message.subject
                    )

                    failed += 1
                    self.stdout.write(self.style.ERROR(f'ERROR: {str(e)}'))

            # Итоги
            self.stdout.write(self.style.SUCCESS(f'Готово! Успешно: {success}, Ошибок: {failed}'))

        except apps.get_model('mailings', 'Mailing').DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Рассылка с ID {mailing_id} не найдена'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {str(e)}'))

