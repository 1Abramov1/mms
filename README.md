# 📧 MMS - Система управления рассылками

Django-приложение для создания, управления и отслеживания email-рассылок.

## 🚀 Быстрый старт

```bash
git clone <ваш-репозиторий>
cd mms
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

Перейдите: http://127.0.0.1:8000

📊 Основные функции

Управление клиентами

· Добавление/редактирование/удаление клиентов
· Уникальные email-адреса
· Группировка получателей

Создание рассылок

· Настройка времени начала и окончания
· Выбор шаблонов сообщений
· Гибкий выбор получателей
· Статусы: Создана/Запущена/Завершена

Отправка и мониторинг

· Ручной запуск: python manage.py send_mailing <ID>
· Автоматическая проверка времени
· Детальные логи отправок
· Статистика успешных/неуспешных отправок

Главная страница

· Общее количество рассылок
· Активные рассылки (с учетом времени)
· Количество уникальных клиентов

🛠 Структура проекта
mms/
├── apps/
│   ├── clients/          # Управление клиентами
│   ├── mailings/         # Рассылки и логи
│   └── mailing_messages/ # Шаблоны писем
├── config/               # Настройки Django
└── templates/            # HTML шаблоны

⚙️ Конфигурация

Добавьте в settings.py:
# SMTP настройки
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'ваш-email@gmail.com'
EMAIL_HOST_PASSWORD = 'ваш-пароль'
DEFAULT_FROM_EMAIL = 'ваш-email@gmail.com'

# Временная зона
TIME_ZONE = 'Europe/Moscow'
USE_TZ = True

📁 Модели

Client

· full_name - ФИО
· email - Email (уникальный)
· comment - Комментарий

Mailing

· start_time, end_time - Время рассылки
· status - Статус (Создана/Запущена/Завершена)
· message - Шаблон письма
· recipients - Получатели

MailingLog

· mailing - Ссылка на рассылку
· client - Получатель
· status - Успешно/Не успешно
· server_response - Ответ сервера
· attempt_time - Время отправки

🔧 Команды
# Запуск рассылки
python manage.py send_mailing 1

# Создание суперпользователя
python manage.py createsuperuser

# Миграции
python manage.py makemigrations
python manage.py migrate

📞 Контакты
‍💻 Разработчик

Абрамов Александр

· GitHub: @1Abramov1

· Поддержка: support@example.com

---

⭐️ Поставьте звезду, если проект полезен!
