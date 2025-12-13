from django import forms
from .models import Message


class MessageForm(forms.ModelForm):
    """Форма для создания и редактирования сообщения"""

    class Meta:
        model = Message
        fields = ['subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите тему письма...'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Введите текст сообщения...',
                'rows': 10
            }),
        }
        labels = {
            'subject': 'Тема письма',
            'body': 'Тело письма',
        }
        help_texts = {
            'subject': 'Краткое описание содержания письма',
            'body': 'Полный текст сообщения',
        }

    def clean_subject(self):
        """Проверка темы письма"""
        subject = self.cleaned_data['subject']
        if not subject.strip():
            raise forms.ValidationError('Тема письма не может быть пустой')
        return subject.strip()

    def clean_body(self):
        """Проверка тела письма"""
        body = self.cleaned_data['body']
        if not body.strip():
            raise forms.ValidationError('Тело письма не может быть пустым')
        return body.strip()