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

        # Исправлено: переменные в нижнем регистре
        mailing_model = apps.get_model('mailings', 'Mailing')
        mailing_log_model = apps.get_model('mailings', 'MailingLog')

        try:
            mailing = mailing_model.objects.get(id=mailing_id)

            # ИНИЦИАЦИЯ: проверка времени согласно ТЗ
            if current_time < mailing.start_time:
                self.stderr.write(
                    self.style.ERROR(
                        f'Ошибка: Текущее время ({current_time.strftime("%Y-%m-%d %H:%M")}) '
                        f'раньше времени начала рассылки ({mailing.start_time.strftime("%Y-%m-%d %H:%M")})'
                    )
                )
                return

            if mailing.end_time and current_time > mailing.end_time:
                self.stderr.write(
                    self.style.ERROR(
                        f'Ошибка: Текущее время ({current_time.strftime("%Y-%m-%d %H:%M")}) '
                        f'позже времени окончания рассылки ({mailing.end_time.strftime("%Y-%m-%d %H:%M")})'
                    )
                )
                return

            self.stdout.write(self.style.SUCCESS(
                f'Запуск рассылки ID {mailing_id}: "{mailing.message.subject}"'
            ))
            self.stdout.write(f'Время проверки пройдено: {current_time.strftime("%Y-%m-%d %H:%M")}')

            # ОПРЕДЕЛЕНИЕ ПОЛУЧАТЕЛЕЙ: выбираем всех клиентов, связанных с этой рассылкой
            clients = mailing.recipients.all()
            self.stdout.write(f'Найдено получателей: {clients.count()}')

            if clients.count() == 0:
                self.stderr.write(self.style.WARNING('Предупреждение: Нет получателей для рассылки'))
                return

            successful_sends = 0
            failed_sends = 0

            # ОТПРАВКА ПИСЕМ: для каждого клиента
            for client in clients:
                try:
                    self.stdout.write(f'Отправка клиенту: {client.email}...', ending=' ')

                    # Отправка письма с помощью send_mail()
                    mail.send_mail(
                        subject=mailing.message.subject,
                        message=mailing.message.body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[client.email],
                        fail_silently=False,
                    )

                    # В случае успеха создается запись о попытке со статусом 'Успешно'
                    mailing_log_model.objects.create(
                        mailing=mailing,
                        client=client,
                        status='Успешно',  # Используем строковое значение
                        sent_at=timezone.now(),
                    )

                    successful_sends += 1
                    self.stdout.write(self.style.SUCCESS('Успешно'))

                except Exception as e:  # Исправлено: правильный отступ для except
                    # При ошибке создается запись со статусом 'Не успешно' и текстом ошибки
                    mailing_log_model.objects.create(
                        mailing=mailing,
                        client=client,
                        status='Не успешно',  # Используем строковое значение
                        error_message=str(e),
                        sent_at=timezone.now(),
                    )

                    failed_sends += 1
                    self.stdout.write(self.style.ERROR(f'Ошибка: {str(e)}'))

            # Итоговая статистика (вынесено из цикла for)
            result_message = f"Отправлено успешно: {successful_sends}, с ошибками: {failed_sends}"

            if successful_sends > 0 or failed_sends > 0:
                self.stdout.write(self.style.SUCCESS(f'Рассылка завершена: {result_message}'))
                logger.info(f"Рассылка {mailing.id}: {result_message}")
            else:
                self.stdout.write(self.style.WARNING('Рассылка не выполнена (нет получателей)'))


        except mailing_model.DoesNotExist:  # Исправлено: правильная ссылка на модель
            self.stderr.write(self.style.ERROR(f'Ошибка: Рассылка с ID {mailing_id} не найдена'))
        except Exception as e:  # Этот блок except должен быть после блока DoesNotExist
            self.stderr.write(self.style.ERROR(f'Критическая ошибка: {str(e)}'))