# 🎯 GeminiVoiceConnect - AI Call Center Dashboard

## 📋 Описание проекта

GeminiVoiceConnect - это современная система управления колл-центром с искусственным интеллектом, включающая веб-дашборд для мониторинга звонков в реальном времени и бэкенд API для управления данными.

### 🌟 Основные возможности

- 📊 **Дашборд в реальном времени** - мониторинг активных звонков, кампаний и системных метрик
- 🤖 **AI-интеграция** - анализ настроений и автоматическая обработка звонков
- 📱 **SMS-управление** - отправка и управление SMS-кампаниями
- 👥 **Управление клиентами** - полная CRM-функциональность
- 📈 **Аналитика** - детальные отчеты и метрики производительности
- 🔄 **WebSocket** - обновления в реальном времени
- 🛡️ **Безопасность** - JWT-аутентификация и авторизация

## 🏗️ Архитектура системы

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (React +      │◄──►│  (Node.js +     │◄──►│   (SQLite +     │
│   TypeScript)   │    │   Express)      │    │   Prisma)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
   Port 12001              Port 3001              dev.db файл
```

## 🚀 Быстрый старт

### 📋 Предварительные требования

Убедитесь, что у вас установлены следующие компоненты:

- **Node.js** версии 18.0 или выше
- **npm** версии 8.0 или выше
- **Git** для клонирования репозитория

### 📥 Установка

#### 1. Клонирование репозитория

```bash
git clone https://github.com/freezingcoldice/My-project-.git
cd My-project-
```

#### 2. Установка зависимостей бэкенда

```bash
cd backend
npm install
```

#### 3. Настройка базы данных

```bash
# Генерация Prisma клиента
npx prisma generate

# Применение миграций базы данных
npx prisma migrate dev --name init

# Заполнение базы данных тестовыми данными
npx prisma db seed
```

#### 4. Настройка переменных окружения

Создайте файл `.env` в папке `backend`:

```bash
# Создание .env файла
cat > .env << 'EOF'
# Database
DATABASE_URL="file:./dev.db"

# JWT Secret
JWT_SECRET="your-super-secret-jwt-key-change-this-in-production"

# Server Configuration
PORT=3001
NODE_ENV=development

# CORS Configuration
FRONTEND_URL="http://localhost:12001"

# API Configuration
API_VERSION="v1"
EOF
```

#### 5. Установка зависимостей фронтенда

```bash
cd ../dashboard
npm install
```

## 🖥️ Запуск приложения

### 🔧 Режим разработки

#### 1. Запуск бэкенда

```bash
cd backend
npm run dev
```

Бэкенд будет доступен по адресу: `http://localhost:3001`

#### 2. Запуск фронтенда (в новом терминале)

```bash
cd dashboard
npm run dev -- --host 0.0.0.0 --port 12001
```

Фронтенд будет доступен по адресу: `http://localhost:12001`

### 🚀 Продакшн режим

#### 1. Сборка фронтенда

```bash
cd dashboard
npm run build
```

#### 2. Запуск в продакшн режиме

```bash
# Бэкенд
cd backend
npm start

# Фронтенд (статические файлы)
cd dashboard
npm run preview
```

### 🔄 Запуск в фоновом режиме

Для запуска сервисов в фоновом режиме используйте `nohup`:

```bash
# Бэкенд в фоне
cd backend
nohup npm run dev > backend.log 2>&1 &

# Фронтенд в фоне
cd dashboard
nohup npm run dev -- --host 0.0.0.0 --port 12001 > frontend.log 2>&1 &
```

## 🔐 Аутентификация

### Тестовые учетные данные

Для входа в систему используйте следующие данные:

- **Email:** `admin@geminivoice.com`
- **Пароль:** `demo123`

### API Endpoints

#### Аутентификация
- `POST /api/auth/login` - Вход в систему
- `POST /api/auth/register` - Регистрация
- `POST /api/auth/refresh` - Обновление токена

#### Дашборд
- `GET /api/dashboard/stats` - Общая статистика
- `GET /api/dashboard/calls/live` - Активные звонки
- `GET /api/dashboard/analytics` - Аналитические данные

#### Управление
- `GET /api/campaigns` - Список кампаний
- `GET /api/customers` - Список клиентов
- `GET /api/calls` - История звонков

## 📊 Структура проекта

```
My-project-/
├── 📁 backend/                 # Серверная часть
│   ├── 📁 prisma/             # Схема базы данных
│   │   ├── schema.prisma      # Prisma схема
│   │   ├── migrations/        # Миграции БД
│   │   └── seed.js           # Тестовые данные
│   ├── 📁 src/               # Исходный код бэкенда
│   │   ├── 📁 routes/        # API маршруты
│   │   ├── 📁 middleware/    # Промежуточное ПО
│   │   ├── 📁 services/      # Бизнес-логика
│   │   └── server.js         # Главный файл сервера
│   ├── package.json          # Зависимости бэкенда
│   └── .env                  # Переменные окружения
│
├── 📁 dashboard/              # Клиентская часть
│   ├── 📁 src/               # Исходный код фронтенда
│   │   ├── 📁 components/    # React компоненты
│   │   ├── 📁 stores/        # Zustand хранилища
│   │   ├── 📁 services/      # API клиенты
│   │   ├── 📁 types/         # TypeScript типы
│   │   └── main.tsx          # Точка входа
│   ├── package.json          # Зависимости фронтенда
│   ├── vite.config.ts        # Конфигурация Vite
│   └── tsconfig.json         # Конфигурация TypeScript
│
└── README.md                 # Этот файл
```

## 🛠️ Технологический стек

### Frontend
- **React 18** - UI библиотека
- **TypeScript** - Типизированный JavaScript
- **Vite** - Сборщик и dev-сервер
- **Zustand** - Управление состоянием
- **Tailwind CSS** - CSS фреймворк
- **Recharts** - Библиотека графиков
- **Lucide React** - Иконки

### Backend
- **Node.js** - Серверная платформа
- **Express.js** - Web фреймворк
- **Prisma** - ORM для работы с БД
- **SQLite** - База данных
- **JWT** - Аутентификация
- **bcryptjs** - Хеширование паролей
- **Socket.IO** - WebSocket соединения

## 🔧 Конфигурация

### Настройка портов

По умолчанию используются следующие порты:
- **Frontend:** 12001
- **Backend:** 3001

Для изменения портов:

1. **Frontend:** Измените в `package.json` или используйте флаг `--port`
2. **Backend:** Измените переменную `PORT` в `.env` файле

### Настройка CORS

В файле `backend/.env` настройте:

```env
FRONTEND_URL="http://localhost:12001"
```

### Настройка базы данных

Для использования другой базы данных измените `DATABASE_URL` в `.env`:

```env
# PostgreSQL
DATABASE_URL="postgresql://user:password@localhost:5432/database"

# MySQL
DATABASE_URL="mysql://user:password@localhost:3306/database"
```

## 🧪 Тестирование

### Проверка работоспособности

#### 1. Проверка бэкенда

```bash
curl http://localhost:3001/api/health
```

Ожидаемый ответ:
```json
{
  "status": "ok",
  "timestamp": "2025-06-01T20:00:00.000Z",
  "uptime": 123.456
}
```

#### 2. Проверка аутентификации

```bash
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@geminivoice.com","password":"demo123"}'
```

#### 3. Проверка фронтенда

Откройте браузер и перейдите по адресу: `http://localhost:12001`

### Функциональное тестирование

1. **Вход в систему** - используйте тестовые данные
2. **Дашборд** - проверьте отображение метрик
3. **Реальное время** - обновления каждые 5 секунд
4. **Навигация** - переключение между разделами
5. **API вызовы** - проверка сетевых запросов в DevTools

## 🐛 Устранение неполадок

### Частые проблемы

#### 1. Ошибка "Port already in use"

```bash
# Найти процесс, использующий порт
lsof -i :3001
lsof -i :12001

# Завершить процесс
kill -9 <PID>
```

#### 2. Ошибки базы данных

```bash
# Пересоздать базу данных
cd backend
rm -f dev.db
npx prisma migrate reset --force
npx prisma db seed
```

#### 3. Ошибки зависимостей

```bash
# Очистить кеш и переустановить
rm -rf node_modules package-lock.json
npm install
```

#### 4. CORS ошибки

Проверьте настройки в `backend/.env`:
```env
FRONTEND_URL="http://localhost:12001"
```

### Логи и отладка

#### Просмотр логов

```bash
# Логи бэкенда
tail -f backend.log

# Логи фронтенда
tail -f frontend.log
```

#### Режим отладки

```bash
# Бэкенд с отладкой
cd backend
DEBUG=* npm run dev

# Фронтенд с подробными логами
cd dashboard
npm run dev -- --debug
```

## 📈 Мониторинг и метрики

### Системные метрики

Дашборд отображает следующие метрики в реальном времени:

- **CPU Usage** - Загрузка процессора
- **Memory Usage** - Использование памяти
- **GPU Usage** - Загрузка видеокарты
- **Uptime** - Время работы системы

### Бизнес-метрики

- **Total Calls** - Общее количество звонков
- **Active Campaigns** - Активные кампании
- **Total Contacts** - Общее количество контактов
- **Conversion Rate** - Коэффициент конверсии

### WebSocket события

Система использует WebSocket для обновлений в реальном времени:

- `call:started` - Начало звонка
- `call:ended` - Завершение звонка
- `system:update` - Обновление системных метрик
- `campaign:update` - Обновление кампании

## 🔒 Безопасность

### Рекомендации по безопасности

1. **Измените JWT_SECRET** в продакшн среде
2. **Используйте HTTPS** для продакшн развертывания
3. **Настройте firewall** для ограничения доступа
4. **Регулярно обновляйте** зависимости
5. **Используйте переменные окружения** для секретов

### Настройка HTTPS

```bash
# Генерация SSL сертификата
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

## 🚀 Развертывание

### Docker развертывание

Создайте `Dockerfile` для каждого сервиса:

```dockerfile
# Backend Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3001
CMD ["npm", "start"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "3001:3001"
    environment:
      - DATABASE_URL=file:./dev.db
      - JWT_SECRET=your-secret-key
    
  frontend:
    build: ./dashboard
    ports:
      - "12001:12001"
    depends_on:
      - backend
```

### Облачное развертывание

#### Heroku

```bash
# Установка Heroku CLI
npm install -g heroku

# Создание приложения
heroku create your-app-name

# Развертывание
git push heroku main
```

#### Vercel (Frontend)

```bash
# Установка Vercel CLI
npm install -g vercel

# Развертывание
cd dashboard
vercel --prod
```

## 📚 API Документация

### Базовый URL

```
http://localhost:3001/api
```

### Заголовки аутентификации

```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### Основные эндпоинты

#### Аутентификация

```http
POST /auth/login
Content-Type: application/json

{
  "email": "admin@geminivoice.com",
  "password": "demo123"
}
```

#### Получение статистики

```http
GET /dashboard/stats
Authorization: Bearer <token>
```

#### Активные звонки

```http
GET /dashboard/calls/live?limit=10
Authorization: Bearer <token>
```

### Формат ответов

Все API ответы имеют следующий формат:

```json
{
  "success": true,
  "data": {
    // Данные ответа
  },
  "message": "Success message",
  "timestamp": "2025-06-01T20:00:00.000Z"
}
```

## 🤝 Вклад в проект

### Как внести вклад

1. **Fork** репозитория
2. **Создайте** ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. **Зафиксируйте** изменения (`git commit -m 'Add amazing feature'`)
4. **Отправьте** в ветку (`git push origin feature/amazing-feature`)
5. **Откройте** Pull Request

### Стандарты кода

- Используйте **TypeScript** для типизации
- Следуйте **ESLint** правилам
- Пишите **тесты** для новой функциональности
- Документируйте **API изменения**

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.

## 📞 Поддержка

Если у вас возникли вопросы или проблемы:

1. **Проверьте** раздел "Устранение неполадок"
2. **Создайте** Issue в GitHub
3. **Свяжитесь** с командой разработки

## 🎯 Дорожная карта

### Планируемые функции

- [ ] **Мобильное приложение** - React Native версия
- [ ] **Расширенная аналитика** - ML-модели для прогнозирования
- [ ] **Интеграции** - CRM системы и внешние API
- [ ] **Масштабирование** - Микросервисная архитектура
- [ ] **Тестирование** - Автоматизированные тесты

### Версии

- **v1.0.0** - Базовая функциональность ✅
- **v1.1.0** - WebSocket интеграция ✅
- **v1.2.0** - Улучшенная аналитика (в разработке)
- **v2.0.0** - Мобильное приложение (планируется)

---

## 🏆 Статус проекта

**Статус:** ✅ Готов к использованию  
**Версия:** v1.1.0  
**Последнее обновление:** 01.06.2025  

### Проверенная функциональность

- ✅ Аутентификация и авторизация
- ✅ Дашборд в реальном времени
- ✅ API интеграция
- ✅ WebSocket соединения
- ✅ База данных и миграции
- ✅ Системные метрики
- ✅ Responsive дизайн

**Система полностью функциональна и готова к использованию!** 🚀