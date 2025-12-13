from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Message
from .forms import MessageForm


class MessageListView(LoginRequiredMixin, ListView):
    """Список всех сообщений"""
    model = Message
    template_name = 'mailing_messages/message_list.html'
    context_object_name = 'message_list'
    paginate_by = 10

    def get_queryset(self):
        return Message.objects.all().order_by('-created_at')


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Создание нового сообщения"""
    model = Message
    form_class = MessageForm
    template_name = 'mailing_messages/message_form.html'
    success_url = reverse_lazy('mailing_messages:message_list')

    def form_valid(self, form):
        # Устанавливаем создателя сообщения
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Сообщение успешно создано!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class MessageDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о сообщении"""
    model = Message
    template_name = 'mailing_messages/message_detail.html'
    context_object_name = 'message'


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование сообщения"""
    model = Message
    form_class = MessageForm
    template_name = 'mailing_messages/message_form.html'

    def get_success_url(self):
        messages.success(self.request, 'Сообщение успешно обновлено!')
        return reverse_lazy('mailing_messages:message_list')

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление сообщения"""
    model = Message
    template_name = 'mailing_messages/message_confirm_delete.html'
    success_url = reverse_lazy('mailing_messages:message_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Сообщение успешно удалено!')
        return super().delete(request, *args, **kwargs)


@login_required
def message_preview(request, pk):
    """Предпросмотр сообщения"""
    message = get_object_or_404(Message, pk=pk)
    return render(request, 'mailing_messages/message_preview.html', {'message': message})
