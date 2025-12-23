from django import forms
from django.core.exceptions import ValidationError
from .models import Client


class ClientForm(forms.ModelForm):
    """Форма для создания и редактирования клиента"""

    class Meta:
        model = Client
        fields = ['email', 'full_name', 'comment']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@email.com'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Иванов Иван Иванович'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Дополнительная информация...',
                'rows': 4
            }),
        }
        labels = {
            'email': 'Email адрес',
            'full_name': 'Ф. И. О.',
            'comment': 'Комментарий',
        }

    def clean_email(self):
        """Проверка уникальности email"""
        email = self.cleaned_data['email']

        # Проверяем, существует ли клиент с таким email
        if Client.objects.filter(email=email).exists():
            # Если редактируем существующий объект, пропускаем проверку
            if self.instance and self.instance.email == email:
                return email
            raise ValidationError('Клиент с таким email уже существует')

        return email