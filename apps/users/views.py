from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView
from django.utils import timezone
import hashlib

from .forms import UserRegisterForm, UserLoginForm, PasswordResetRequestForm, SetNewPasswordForm, UserProfileForm
from .models import User


class RegisterView(CreateView):
    """Регистрация пользователя"""
    form_class = UserRegisterForm
    template_name = 'users/auth/register.html'
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        # Сохраняем пользователя
        user = form.save()

        # Отправляем письмо для подтверждения email
        user.send_verification_email(self.request)

        messages.success(
            self.request,
            'Регистрация успешна! Проверьте вашу почту для подтверждения email.'
        )
        return super().form_valid(form)


class LoginView(FormView):
    """Вход пользователя"""
    form_class = UserLoginForm
    template_name = 'users/auth/login.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        # Аутентифицируем пользователя
        user = form.get_user()
        login(self.request, user)

        messages.success(
            self.request,
            f'Добро пожаловать, {user.username}!'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Ошибка входа. Проверьте правильность данных.'
        )
        return super().form_invalid(form)


@login_required
def logout_view(request):
    """Выход пользователя"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('home')


def verify_email_view(request, token):
    """Подтверждение email"""
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    try:
        user = User.objects.get(
            verification_token=token_hash,
            email_verified=False
        )

        if user.is_token_valid():
            user.email_verified = True
            user.verification_token = None
            user.token_created_at = None
            user.save()

            messages.success(
                request,
                'Ваш email успешно подтвержден! Теперь вы можете войти в систему.'
            )
        else:
            messages.error(
                request,
                'Срок действия ссылки истек. Запросите новое письмо для подтверждения.'
            )

    except User.DoesNotExist:
        messages.error(
            request,
            'Неверная или устаревшая ссылка подтверждения.'
        )

    return redirect('users:login')


def resend_verification_view(request):
    """Повторная отправка письма для подтверждения email"""
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email, email_verified=False)
            user.send_verification_email(request)

            messages.success(
                request,
                'Письмо для подтверждения email отправлено повторно.'
            )

        except User.DoesNotExist:

                messages.error(
                    request,
                'Пользователь с таким email не найден или email уже подтвержден.'
                )


        return render(request, 'users/auth/resend_verification.html')


class PasswordResetView(FormView):
    """Запрос сброса пароля"""
    form_class = PasswordResetRequestForm
    template_name = 'users/auth/password_reset.html'
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        user = User.objects.get(email=email)

        # Отправляем письмо для сброса пароля
        user.send_password_reset_email(self.request)

        messages.success(
            self.request,
            'Письмо с инструкцией по сбросу пароля отправлено на ваш email.'
        )
        return super().form_valid(form)


def password_reset_confirm_view(request, token):
    """Подтверждение сброса пароля"""
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    try:
        user = User.objects.get(verification_token=token_hash)

        if not user.is_token_valid():
            messages.error(
                request,
                'Срок действия ссылки истек. Запросите новый сброс пароля.'
            )
            return redirect('users:password_reset')

        if request.method == 'POST':
            form = SetNewPasswordForm(request.POST)
            if form.is_valid():
                # Устанавливаем новый пароль
                new_password = form.cleaned_data['new_password1']
                user.set_password(new_password)
                user.verification_token = None
                user.token_created_at = None
                user.save()

                messages.success(
                    request,
                    'Пароль успешно изменен! Теперь вы можете войти с новым паролем.'
                )
                return redirect('users:login')
        else:
            form = SetNewPasswordForm()

        return render(request, 'users/auth/password_reset_confirm.html', {
            'form': form,
            'token': token
        })

    except User.DoesNotExist:
        messages.error(
            request,
            'Неверная или устаревшая ссылка сброса пароля.'
        )
        return redirect('users:password_reset')


@login_required
def profile_view(request):
    """Профиль пользователя"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()

            # Если email изменился, отправляем письмо для подтверждения
            if 'email' in form.changed_data:
                user.email_verified = False
                user.save()
                user.send_verification_email(request)

                messages.success(
                    request,
                    'Профиль обновлен! На новый email отправлено письмо для подтверждения.'
                )
            else:
                messages.success(request, 'Профиль успешно обновлен.')

            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'users/auth/profile.html', {
        'form': form,
        'user': request.user
    })


@login_required
def profile_delete_view(request):
    """Удаление профиля"""
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()

        messages.success(
            request,
            'Ваш аккаунт успешно удален.'
        )
        return redirect('home')

    return render(request, 'users/auth/profile_delete.html')
