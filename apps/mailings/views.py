from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from .models import Mailing
from .forms import MailingForm


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
