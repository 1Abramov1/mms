from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Mailing


class MailingForm(forms.ModelForm):
    """Форма для создания и редактирования рассылки"""

    class Meta:
        model = Mailing
        fields = ['start_time', 'end_time', 'message', 'recipients']
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                    'min': timezone.now().strftime('%Y-%m-%dT%H:%M')
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'end_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'message': forms.Select(attrs={'class': 'form-control'}),
            'recipients': forms.SelectMultiple(
                attrs={
                    'class': 'form-control',
                    'size': '10'
                }
            ),
        }
        labels = {
            'start_time': 'Дата и время начала',
            'end_time': 'Дата и время окончания',
            'message': 'Сообщение',
            'recipients': 'Получатели',
        }
        help_texts = {'start_time': 'Рассылка начнется в указанное время',
                      'end_time': 'Рассылка завершится в указанное время',
                      'recipients': 'Выберите получателей (удерживайте Ctrl для множественного выбора)',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Настраиваем поле recipients для отображения email клиентов
        from apps.clients.models import Client
        self.fields['recipients'].queryset = Client.objects.all()
        self.fields['recipients'].label_from_instance = lambda obj: f"{obj.full_name} ({obj.email})"

    def clean_start_time(self):
        """Валидация start_time"""
        start_time = self.cleaned_data['start_time']

        # Проверка: start_time не может быть в прошлом
        if start_time and start_time < timezone.now():
            raise ValidationError('Дата начала не может быть в прошлом')

        return start_time

    def clean_end_time(self):
        """Валидация end_time"""
        end_time = self.cleaned_data['end_time']
        start_time = self.cleaned_data.get('start_time')

        if start_time and end_time:
            # Проверка: start_time должен быть раньше end_time
            if start_time >= end_time:
                raise ValidationError('Дата окончания должна быть позже даты начала')

        return end_time

    def clean(self):
        """Общая валидация формы"""
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        # Проверка наличия получателей
        recipients = cleaned_data.get('recipients')
        if not recipients:
            raise ValidationError({
                'recipients': 'Выберите хотя бы одного получателя'
            })

        return cleaned_data

    def save(self, commit=True):
        """Сохранение формы с установкой created_by"""
        mailing = super().save(commit=False)

        if self.user and not mailing.pk:  # Если создается новый объект
            mailing.created_by = self.user

        if commit:
            mailing.save()
            self.save_m2m()  # Сохраняем ManyToMany отношения

        return mailing