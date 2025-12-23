from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from .models import User


class UserRegisterForm(UserCreationForm):
    """Форма регистрации пользователя"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email'
        }),
        help_text='Обязательное поле. На этот адрес придет письмо для подтверждения.'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Придумайте логин'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Придумайте пароль'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Повторите пароль'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email


class UserLoginForm(AuthenticationForm):
    """Форма входа пользователя"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Логин или email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пароль'
        })
    )

    def confirm_login_allowed(self, user):
        """Проверяем, подтвержден ли email пользователя"""
        super().confirm_login_allowed(user)

        if not user.email_verified:
            raise ValidationError(
                'Ваш email не подтвержден. '
                'Проверьте вашу почту и перейдите по ссылке в письме.',
                code='email_not_verified'
            )


class PasswordResetRequestForm(forms.Form):
    """Форма запроса сброса пароля"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email не найден.')
        return email


class SetNewPasswordForm(forms.Form):
    """Форма установки нового пароля"""
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Новый пароль'
        }),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Подтвердите новый пароль'
        }),
        strip=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', "Пароли не совпадают.")

        # Валидация пароля
        if password1:
            try:
                password_validation.validate_password(password1)
            except ValidationError as error:
                self.add_error('new_password1', error)

        return cleaned_data


class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля"""

    class Meta:
               model = User
               fields = ['first_name', 'last_name', 'email']
               widgets = {
                   'first_name': forms.TextInput(attrs={'class': 'form-control'}),
                   'last_name': forms.TextInput(attrs={'class': 'form-control'}),
                   'email': forms.EmailInput(attrs={'class': 'form-control'}),
               }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Проверяем, не используется ли email другим пользователем
        if User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise ValidationError('Этот email уже используется другим пользователем.')

        # Если email изменился, сбрасываем подтверждение
        if email != self.instance.email:
            self.instance.email_verified = False
        return email