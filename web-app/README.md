# 🌐 Веб-интерфейс ППСД

Современный веб-интерфейс для системы проверки сертификатных данных (ППСД) с расширенной аналитикой и уведомлениями.

## 🚀 Возможности

### 📊 Дашборд и аналитика
- **Интерактивные графики** - динамика поступлений, распределение по статусам
- **KPI метрики** - статистика с изменениями за период
- **Поток обработки** - визуализация этапов проверки материалов
- **Фильтрация данных** - по периоду, поставщику, марке материала

### 🔔 Система уведомлений
- **Email уведомления** - критические события и изменения статусов
- **Telegram бот** - мгновенные уведомления в мессенджер
- **Web push** - браузерные уведомления (в разработке)

### 📱 Адаптивный дизайн
- **Responsive layout** - работает на всех устройствах
- **Material Design** - современный и интуитивный интерфейс
- **PWA ready** - возможность установки как приложение

## 🏗️ Архитектура

```
web-app/
├── backend/                 # Серверная часть
│   ├── web_server.py       # Flask веб-сервер
│   ├── analytics_api.py    # API аналитики
│   └── notifications.py    # Система уведомлений
├── frontend/               # Клиентская часть
├── templates/              # HTML шаблоны
│   ├── index.html         # Главная страница
│   └── dashboard.html     # Дашборд аналитики
├── static/                 # Статические файлы
└── README.md              # Эта документация
```

## 🛠️ Установка и запуск

### Быстрый старт

1. **Установка зависимостей:**
```bash
pip install -r requirements_web.txt
```

2. **Запуск всех сервисов:**
```bash
python start_web_services.py
```

3. **Доступ к интерфейсу:**
- 🏠 Главная страница: http://localhost:5000
- 📊 Дашборд: http://localhost:5000/dashboard
- 🔧 API документация: http://localhost:8000/docs

### Ручной запуск сервисов

1. **Основной API (порт 8000):**
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

2. **Аналитический API (порт 8001):**
```bash
python web-app/backend/analytics_api.py
```

3. **Веб-интерфейс (порт 5000):**
```bash
python web-app/backend/web_server.py
```

4. **Telegram бот (опционально):**
```bash
export TELEGRAM_BOT_TOKEN=your_token
python web-app/backend/notifications.py
```

## ⚙️ Конфигурация

### Переменные окружения

```bash
# Telegram бот
export TELEGRAM_BOT_TOKEN=your_bot_token

# Email уведомления
export SMTP_SERVER=smtp.company.com
export SMTP_PORT=587
export SMTP_USERNAME=username
export SMTP_PASSWORD=password
export FROM_EMAIL=noreply@company.com

# База данных (если отличается от основной)
export DATABASE_URL=sqlite:///ppsd.db
```

### Настройка .env файла

Создайте файл `.env` в корневой директории:

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com

# Веб-сервер
WEB_HOST=0.0.0.0
WEB_PORT=5000
DEBUG=True

# API
API_HOST=0.0.0.0
API_PORT=8000
```

## 📊 API Endpoints

### Основной API (порт 8000)
- `GET /` - Информация о системе
- `GET /materials` - Список материалов
- `GET /statistics` - Общая статистика
- `POST /materials` - Добавление материала
- `PUT /materials/{id}` - Обновление материала

### Аналитический API (порт 8001)
- `GET /statistics` - Расширенная статистика
- `GET /materials/distribution` - Распределение по статусам
- `GET /suppliers/stats` - Статистика поставщиков
- `GET /materials/timeline` - Временная линия
- `GET /kpi/dashboard` - KPI для дашборда
- `GET /export/analytics-report` - Экспорт отчета

## 🤖 Telegram бот

### Команды бота
- `/start` - Приветствие и инструкции
- `/status` - Текущий статус системы
- `/help` - Помощь

### Настройка уведомлений
1. Создайте бота через @BotFather
2. Получите токен
3. Установите переменную `TELEGRAM_BOT_TOKEN`
4. Запустите бота: `python web-app/backend/notifications.py`
5. Обратитесь к администратору для связки аккаунта

## 📈 Мониторинг

### Проверка состояния сервисов
```bash
# Проверка веб-сервера
curl http://localhost:5000/health

# Проверка основного API
curl http://localhost:8000/

# Проверка аналитического API
curl http://localhost:8001/
```

### Логи
Логи всех сервисов выводятся в консоль при запуске через `start_web_services.py`

## 🔒 Безопасность

### Рекомендации
- Используйте HTTPS в продакшене
- Настройте CORS для конкретных доменов
- Используйте переменные окружения для секретов
- Регулярно обновляйте зависимости

### Аутентификация
- Веб-интерфейс использует сессии Flask
- API поддерживает JWT токены
- Планируется интеграция с LDAP/AD

## 🐛 Устранение неисправностей

### Частые проблемы

1. **Порт уже занят:**
```bash
# Найти процесс
netstat -ano | findstr :5000
# Завершить процесс
taskkill /PID <PID> /F
```

2. **Ошибка подключения к базе данных:**
- Проверьте, что основное приложение создало БД
- Убедитесь в правильности пути к БД

3. **Telegram бот не отвечает:**
- Проверьте токен
- Убедитесь в доступности интернета
- Проверьте логи на ошибки

4. **Ошибки импорта:**
```bash
# Установка всех зависимостей
pip install -r requirements.txt
pip install -r requirements_web.txt
```

## 🔧 Разработка

### Добавление новых страниц
1. Создайте HTML шаблон в `templates/`
2. Добавьте маршрут в `web_server.py`
3. При необходимости создайте API endpoint

### Добавление новых уведомлений
1. Расширьте `NotificationManager` в `notifications.py`
2. Добавьте новые типы событий
3. Настройте триггеры в основном коде

### Стили и дизайн
- Используйте CSS переменные для цветов
- Следуйте принципам Material Design
- Тестируйте на разных разрешениях

## 📝 TODO

- [ ] PWA манифест и service worker
- [ ] Веб push уведомления
- [ ] Реальные данные для графиков времени обработки
- [ ] Система ролей и разрешений в веб-интерфейсе
- [ ] Экспорт дашборда в PDF
- [ ] Темная тема
- [ ] Многоязычность

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи сервисов
2. Убедитесь в правильности конфигурации
3. Обратитесь к основной документации проекта
4. Создайте issue в репозитории 