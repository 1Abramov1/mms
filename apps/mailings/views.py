from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from .models import Mailing, MailingLog
from .forms import MailingForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .services import MailingService


class MailingListView(LoginRequiredMixin, ListView):
    """Список всех рассылок"""
    model = Mailing
    template_name = 'mailings/mailing_list.html'
    context_object_name = 'mailings'
    paginate_by = 10

    def get_queryset(self):
        # Обновляем статус для всех рассылок перед отображением
        mailings = Mailing.objects.all().order_by('-start_time')
        for mailing in mailings:
            mailing.update_status()
        return mailings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Статистика
        mailings = self.get_queryset()
        context['total_count'] = mailings.count()
        context['created_count'] = mailings.filter(status=Mailing.STATUS_CREATED).count()
        context['started_count'] = mailings.filter(status=Mailing.STATUS_STARTED).count()
        context['completed_count'] = mailings.filter(status=Mailing.STATUS_COMPLETED).count()

        return context


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Создание новой рассылки"""
    model = Mailing
    form_class = MailingForm
    template_name = 'mailings/mailing_form.html'
    success_url = reverse_lazy('mailings:mailing_list')

    def get_form_kwargs(self):
        """Передаем пользователя в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Рассылка успешно создана!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class MailingDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о рассылке"""
    model = Mailing
    template_name = 'mailings/mailing_detail.html'
    context_object_name = 'mailing'

    def get_object(self, queryset=None):
        """
        Получаем объект и обновляем его статус
        Согласно ТЗ: метод update_status() вызывается при просмотре рассылки
        """
        obj = super().get_object(queryset)
        obj.update_status()  # ← пересчёт и сохранение статуса
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mailing = self.object

        # Дополнительная информация
        context['recipients_list'] = mailing.recipients.all()
        context['is_active'] = mailing.is_active()
        context['time_until_start'] = mailing.time_until_start()
        context['duration'] = mailing.duration()

        return context


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование рассылки"""
    model = Mailing
    form_class = MailingForm
    template_name = 'mailings/mailing_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        messages.success(self.request, 'Рассылка успешно обновлена!')
        return reverse_lazy('mailings:mailing_detail', kwargs={'pk': self.object.pk})

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление рассылки"""
    model = Mailing
    template_name = 'mailings/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailings:mailing_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Рассылка успешно удалена!')
        return super().delete(request, *args, **kwargs)


def mailing_stats(request):
    """Статистика по рассылкам"""
    mailings = Mailing.objects.all()

    # Обновляем статус для всех рассылок
    for mailing in mailings:
        mailing.update_status()

    stats = {
        'total': mailings.count(),
        'created': mailings.filter(status=Mailing.STATUS_CREATED).count(),
        'started': mailings.filter(status=Mailing.STATUS_STARTED).count(),
        'completed': mailings.filter(status=Mailing.STATUS_COMPLETED).count(),
    }

    # Процентное соотношение
    if stats['total'] > 0:
        stats['created_percent'] = (stats['created'] / stats['total']) * 100
        stats['started_percent'] = (stats['started'] / stats['total']) * 100
        stats['completed_percent'] = (stats['completed'] / stats['total']) * 100
    else:
        stats['created_percent'] = stats['started_percent'] = stats['completed_percent'] = 0

    return render(request, 'mailings/mailing_stats.html', {'stats': stats})


@login_required
@require_POST
def mailing_start_now(request, pk):
    """
    Ручной запуск рассылки через интерфейс пользователя
    """
    mailing = get_object_or_404(Mailing, pk=pk)
    current_time = timezone.now()

    # Проверяем права
    if not request.user.is_staff and mailing.created_by != request.user:
        messages.error(request, 'У вас нет прав для запуска этой рассылки')
        return redirect('mailings:mailing_detail', pk=pk)

    # Проверяем статус рассылки
    if mailing.status == Mailing.STATUS_COMPLETED:
        messages.warning(request, 'Рассылка уже завершена и не может быть запущена')
        return redirect('mailings:mailing_detail', pk=pk)

    # ПРОВЕРКА ВРЕМЕНИ СОГЛАСНО ТЗ
    if current_time < mailing.start_time:
        messages.error(
            request,
            f'Рассылка не может быть запущена раньше времени начала ({mailing.start_time.strftime("%Y-%m-%d %H:%M")})'
        )
        return redirect('mailings:mailing_detail', pk=pk)

    if mailing.end_time and current_time > mailing.end_time:
        messages.error(
            request,
            f'Рассылка не может быть запущена позже времени окончания ({mailing.end_time.strftime("%Y-%m-%d %H:%M")})'
        )
        return redirect('mailings:mailing_detail', pk=pk)

    # Запускаем рассылку
    success, result_message = MailingService.send_mailing(mailing)

    if success:
        messages.success(request, f'Рассылка запущена: {result_message}')
    else:
        messages.error(request, f'Ошибка запуска: {result_message}')

    return redirect('mailings:mailing_detail', pk=pk)


@login_required
def mailing_send_test(request, pk):
    """
    Отправка тестового письма для проверки
    """
    mailing = get_object_or_404(Mailing, pk=pk)

    # Проверяем права доступа
    if not request.user.is_staff and mailing.created_by != request.user:
        messages.error(request, 'У вас нет прав для тестовой отправки')
        return redirect('mailings:mailing_detail', pk=pk)

    if request.method == 'POST':
        test_email = request.POST.get('test_email', '').strip()

        if test_email:
            success, result_message = MailingService.send_test_email(
                test_email,
                f"[ТЕСТ] {mailing.message.subject}",
                mailing.message.body
            )

            if success:
                messages.success(request, f'Тестовое письмо отправлено: {result_message}')
            else:
                messages.error(request, f'Ошибка отправки: {result_message}')
        else:
            messages.error(request, 'Введите email для тестовой отправки')

    return redirect('mailings:mailing_detail', pk=pk)


@login_required
def mailing_logs(request, pk):
    """
    Просмотр логов отправки
    """
    mailing = get_object_or_404(Mailing, pk=pk)
    """ 
    Проверяем права доступа
    """
    if not request.user.is_staff and mailing.created_by != request.user:
        messages.error(request, 'У вас нет прав для просмотра логов этой рассылки')
        return redirect('mailings:mailing_detail', pk=pk)

    logs = mailing.logs.all().order_by('-sent_at')
    stats = MailingService.get_mailing_stats(mailing)

    return render(request, 'mailings/mailing_logs.html', {
        'mailing': mailing,
        'logs': logs,
        'stats': stats,
    })


@login_required
def mailing_stats_detailed(request, pk):
    """
    Детальная статистика по рассылке
    """
    mailing = get_object_or_404(Mailing, pk=pk)

    # Проверяем права доступа
    if not request.user.is_staff and mailing.created_by != request.user:
        messages.error(request, 'У вас нет прав для просмотра статистики этой рассылки')
        return redirect('mailings:mailing_detail', pk=pk)

    stats = MailingService.get_mailing_stats(mailing)

    # Группировка по статусам
    logs_by_status = {
        'success': mailing.logs.filter(status=MailingLog.STATUS_SUCCESS),
        'failed': mailing.logs.filter(status=MailingLog.STATUS_FAILED),
    }

    # Группировка по времени
    today = timezone.now().date()
    logs_today = mailing.logs.filter(sent_at__date=today).count()

    return render(request, 'mailings/mailing_stats_detailed.html', {
        'mailing': mailing,
        'stats': stats,
        'logs_by_status': logs_by_status,
        'logs_today': logs_today,
    })
