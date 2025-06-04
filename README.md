# 🎯 VoiceConnect Pro - Продвинутая ИИ-платформа колл-центра с Click API

## 📋 Обзор проекта

VoiceConnect Pro - это комплексная платформа колл-центра на базе искусственного интеллекта, специально адаптированная для узбекского рынка. Система включает интеграцию с платежной системой Click, локальную обработку SMS через модули SIM800C и многоязычную поддержку с автоматическим переводом.

### 🌟 Ключевые особенности

- 💳 **Интеграция Click API** - Полная поддержка узбекской платежной системы Click
- 📱 **Локальная SMS обработка** - SIM800C GSM модули вместо Twilio
- 🌐 **Многоязычная поддержка** - 10+ языков включая узбекский
- 🔄 **Автоматический перевод** - Кнопка для перевода всего сайта
- 🤖 **ИИ-автоматизация** - Интеллектуальная обработка звонков и сообщений
- 📊 **Аналитика в реальном времени** - Комплексная панель управления
- 🔒 **Корпоративная безопасность** - Шифрование и контроль доступа

## 🏗️ Архитектура системы

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Фронтенд      │    │   Core API      │    │   Click API     │
│   (React/JS)    │◄──►│   (FastAPI)     │◄──►│   Платежи       │
│   Многоязычный  │    │   ИИ-сервисы    │    │   Подписки      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
   Порт 12000              Порт 8000              Click Webhook
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Переводчик    │    │   SIM800C       │    │   База данных   │
│   Google/Yandex │    │   GSM модули    │    │   PostgreSQL    │
│   API           │    │   Локальные SMS │    │   Redis кэш     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Быстрый старт

### 📋 Предварительные требования

- **Python 3.8+** с pip
- **Node.js 16+** для фронтенда
- **PostgreSQL 12+** для базы данных
- **Redis 6+** для кэширования
- **SIM800C модули** для SMS
- **Click API аккаунт** для платежей

### 📥 Установка

#### 1. Клонирование репозитория

```bash
git clone https://github.com/NigoraAsil/Call-center-.git
cd Call-center-
```

#### 2. Настройка Backend

```bash
cd core-api
pip install -r requirements.txt
python init_db.py
```

#### 3. Настройка Frontend

```bash
cd ../frontend
npm install
npm run build
```

#### 4. Конфигурация API ключей

Создайте файл `config/api_keys.json`:

```json
{
  "openai": {
    "api_key": "ВАШ_OPENAI_API_КЛЮЧ",
    "description": "OpenAI API для ИИ-функций"
  },
  "click": {
    "service_id": "ВАШ_CLICK_SERVICE_ID",
    "secret_key": "ВАШ_CLICK_SECRET_KEY",
    "merchant_id": "ВАШ_CLICK_MERCHANT_ID",
    "description": "Click API для платежей в Узбекистане"
  },
  "google_translate": {
    "api_key": "ВАШ_GOOGLE_TRANSLATE_KEY",
    "description": "Google Translate для автоматического перевода"
  },
  "gsm": {
    "port1": "/dev/ttyUSB0",
    "port2": "/dev/ttyUSB1",
    "baudrate": 9600,
    "description": "SIM800C GSM модули для SMS"
  }
}
```

#### 5. Переменные окружения

Создайте файл `.env`:

```bash
# База данных
DATABASE_URL=postgresql://user:password@localhost/voiceconnect
REDIS_URL=redis://localhost:6379

# Click API
CLICK_SERVICE_ID=ваш_service_id
CLICK_SECRET_KEY=ваш_secret_key
CLICK_MERCHANT_ID=ваш_merchant_id

# Безопасность
JWT_SECRET=ваш_jwt_секрет
ENCRYPTION_KEY=ваш_ключ_шифрования

# GSM модули
GSM_PORT1=/dev/ttyUSB0
GSM_PORT2=/dev/ttyUSB1
GSM_BAUDRATE=9600
```

### 🏃‍♂️ Запуск системы

#### Разработка

```bash
# Backend
cd core-api
python main.py

# Frontend (в новом терминале)
cd frontend
npm start
```

#### Продакшн

```bash
# Docker
docker-compose up -d

# Или вручную
cd core-api
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 💳 Интеграция Click API

### Настройка Click платежей

1. **Регистрация в Click**
   - Зарегистрируйтесь на [click.uz](https://click.uz)
   - Получите Service ID и Secret Key
   - Настройте webhook URL

2. **Конфигурация в системе**
   ```python
   # В config/api_keys.py
   CLICK_CONFIG = {
       "service_id": os.getenv("CLICK_SERVICE_ID"),
       "secret_key": os.getenv("CLICK_SECRET_KEY"),
       "merchant_id": os.getenv("CLICK_MERCHANT_ID"),
       "webhook_url": "https://yourdomain.com/api/v1/payments/click/webhook"
   }
   ```

3. **Тестирование платежей**
   ```bash
   cd core-api
   python test_click_integration.py
   ```

### Поддерживаемые функции Click

- ✅ **Одноразовые платежи** - Обычные покупки
- ✅ **Подписки** - Ежемесячные/годовые планы
- ✅ **Возвраты** - Автоматическая обработка возвратов
- ✅ **Webhook обработка** - Реальное время уведомления
- ✅ **Проверка подписи** - Безопасная валидация
- ✅ **Мультивалютность** - UZS, USD, EUR

### API эндпоинты Click

```http
# Создание платежа
POST /api/v1/payments/click/create-payment
{
  "amount": 50000,
  "description": "Подписка Premium",
  "return_url": "https://yourdomain.com/success"
}

# Создание подписки
POST /api/v1/payments/click/create-subscription
{
  "plan": "premium",
  "tenant_id": "uuid",
  "amount": 100000
}

# Статус платежа
GET /api/v1/payments/click/payment-status/{transaction_id}

# Webhook обработка
POST /api/v1/payments/click/webhook
```

## 📱 SIM800C GSM интеграция

### Настройка оборудования

1. **Подключение модулей**
   ```bash
   # Проверка USB портов
   ls /dev/ttyUSB*
   
   # Должно показать:
   # /dev/ttyUSB0
   # /dev/ttyUSB1
   ```

2. **Конфигурация модулей**
   ```python
   # В core-api/hardware/sim800c_manager.py
   GSM_MODULES = [
       {
           "port": "/dev/ttyUSB0",
           "name": "GSM_MODULE_1",
           "sim_card": "SIM1"
       },
       {
           "port": "/dev/ttyUSB1", 
           "name": "GSM_MODULE_2",
           "sim_card": "SIM2"
       }
   ]
   ```

3. **Тестирование SMS**
   ```bash
   cd core-api
   python check_sms.py
   ```

### Функции GSM модулей

- ✅ **Отправка SMS** - Массовая рассылка
- ✅ **Получение SMS** - Входящие сообщения
- ✅ **Голосовые звонки** - Исходящие вызовы
- ✅ **USSD команды** - Проверка баланса
- ✅ **Мониторинг сигнала** - Качество связи
- ✅ **Автоматическое переключение** - Резервирование

## 🌐 Многоязычная поддержка

### Поддерживаемые языки

1. **Английский** (en) - English
2. **Русский** (ru) - Русский
3. **Узбекский** (uz) - O'zbek
4. **Испанский** (es) - Español
5. **Французский** (fr) - Français
6. **Немецкий** (de) - Deutsch
7. **Итальянский** (it) - Italiano
8. **Португальский** (pt) - Português
9. **Арабский** (ar) - العربية
10. **Китайский** (zh) - 中文

### Автоматический перевод

```javascript
// Кнопка автоматического перевода
function translateWebsite(targetLang) {
    // Использует Google Translate API
    const elements = document.querySelectorAll('[data-translate]');
    elements.forEach(async (element) => {
        const translated = await translateText(element.textContent, targetLang);
        element.textContent = translated;
    });
}

// Определение языка пользователя
function detectUserLanguage() {
    return navigator.language || navigator.userLanguage || 'en';
}
```

### Локализация интерфейса

```json
// translations/uz.json
{
  "dashboard": "Boshqaruv paneli",
  "payments": "To'lovlar", 
  "sms": "SMS xabarlar",
  "calls": "Qo'ng'iroqlar",
  "analytics": "Tahlil",
  "settings": "Sozlamalar",
  "click_payment": "Click to'lov",
  "subscription": "Obuna"
}
```

## 📊 API документация

### Основные эндпоинты

#### Аутентификация
```http
POST /api/v1/auth/login
POST /api/v1/auth/register
POST /api/v1/auth/refresh
GET /api/v1/auth/profile
```

#### ИИ инструменты
```http
GET /api/v1/tools/available
POST /api/v1/tools/execute
GET /api/v1/tools/history
POST /api/v1/tools/chain
```

#### Click платежи
```http
POST /api/v1/payments/click/create-payment
POST /api/v1/payments/click/create-subscription
GET /api/v1/payments/click/payment-status/{id}
POST /api/v1/payments/click/webhook
GET /api/v1/payments/click/subscriptions
```

#### GSM/SMS
```http
POST /api/v1/sms/send
GET /api/v1/sms/status
GET /api/v1/sms/inbox
POST /api/v1/calls/initiate
GET /api/v1/calls/history
GET /api/v1/gsm/status
```

#### Переводы
```http
POST /api/v1/translate/text
GET /api/v1/translate/languages
POST /api/v1/translate/detect
```

### Примеры использования

#### Создание Click платежа

```python
import requests

# Создание платежа
response = requests.post('http://localhost:8000/api/v1/payments/click/create-payment', 
    json={
        "amount": 50000,  # 500 сум
        "description": "Premium подписка",
        "return_url": "https://mysite.com/success",
        "cancel_url": "https://mysite.com/cancel"
    },
    headers={"Authorization": "Bearer YOUR_JWT_TOKEN"}
)

payment_data = response.json()
print(f"Payment URL: {payment_data['payment_url']}")
```

#### Отправка SMS через GSM

```python
import requests

# Отправка SMS
response = requests.post('http://localhost:8000/api/v1/sms/send',
    json={
        "phone": "+998901234567",
        "message": "Sizning buyurtmangiz qabul qilindi!",
        "module": "GSM_MODULE_1"
    },
    headers={"Authorization": "Bearer YOUR_JWT_TOKEN"}
)

sms_result = response.json()
print(f"SMS Status: {sms_result['status']}")
```

#### Автоматический перевод

```python
import requests

# Перевод текста
response = requests.post('http://localhost:8000/api/v1/translate/text',
    json={
        "text": "Hello, how are you?",
        "target_language": "uz",
        "source_language": "en"
    },
    headers={"Authorization": "Bearer YOUR_JWT_TOKEN"}
)

translation = response.json()
print(f"Translated: {translation['translated_text']}")
```

## 🔧 Конфигурация и настройка

### Настройка Click API

1. **Получение учетных данных**
   - Зарегистрируйтесь на [click.uz](https://click.uz)
   - Перейдите в раздел "Для разработчиков"
   - Создайте новый сервис
   - Получите Service ID и Secret Key

2. **Настройка webhook**
   ```bash
   # URL для webhook
   https://yourdomain.com/api/v1/payments/click/webhook
   
   # Методы: POST
   # Формат: JSON
   ```

3. **Тестовые данные**
   ```json
   {
     "service_id": 12345,
     "secret_key": "test_secret_key",
     "test_mode": true
   }
   ```

### Настройка GSM модулей

1. **Установка драйверов**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install usb-modeswitch usb-modeswitch-data
   
   # CentOS/RHEL
   sudo yum install usb_modeswitch usb_modeswitch-data
   ```

2. **Права доступа**
   ```bash
   # Добавить пользователя в группу dialout
   sudo usermod -a -G dialout $USER
   
   # Перезагрузиться или выполнить
   newgrp dialout
   ```

3. **Проверка подключения**
   ```bash
   # Проверить USB устройства
   lsusb | grep -i sim800
   
   # Проверить последовательные порты
   ls -la /dev/ttyUSB*
   ```

### Настройка переводчика

1. **Google Translate API**
   ```bash
   # Установка библиотеки
   pip install google-cloud-translate
   
   # Настройка аутентификации
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
   ```

2. **Yandex Translate API**
   ```bash
   # Получение API ключа
   # https://cloud.yandex.ru/services/translate
   
   # Настройка в config
   YANDEX_TRANSLATE_KEY=your_api_key
   ```

## 🚀 Развертывание

### Docker развертывание

1. **Создание образов**
   ```bash
   # Backend
   docker build -t voiceconnect-api ./core-api
   
   # Frontend  
   docker build -t voiceconnect-frontend ./frontend
   ```

2. **Docker Compose**
   ```yaml
   version: '3.8'
   services:
     api:
       image: voiceconnect-api
       ports:
         - "8000:8000"
       environment:
         - DATABASE_URL=postgresql://user:pass@db:5432/voiceconnect
         - REDIS_URL=redis://redis:6379
       devices:
         - "/dev/ttyUSB0:/dev/ttyUSB0"
         - "/dev/ttyUSB1:/dev/ttyUSB1"
     
     frontend:
       image: voiceconnect-frontend
       ports:
         - "12000:80"
     
     db:
       image: postgres:13
       environment:
         - POSTGRES_DB=voiceconnect
         - POSTGRES_USER=user
         - POSTGRES_PASSWORD=pass
     
     redis:
       image: redis:6-alpine
   ```

3. **Запуск**
   ```bash
   docker-compose up -d
   ```

### Kubernetes развертывание

1. **Конфигурация**
   ```yaml
   # k8s/deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: voiceconnect-api
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: voiceconnect-api
     template:
       metadata:
         labels:
           app: voiceconnect-api
       spec:
         containers:
         - name: api
           image: voiceconnect-api:latest
           ports:
           - containerPort: 8000
           env:
           - name: DATABASE_URL
             valueFrom:
               secretKeyRef:
                 name: voiceconnect-secrets
                 key: database-url
   ```

2. **Развертывание**
   ```bash
   kubectl apply -f k8s/
   ```

### Продакшн настройки

1. **Nginx конфигурация**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location /api/ {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location / {
           proxy_pass http://localhost:12000;
           proxy_set_header Host $host;
       }
   }
   ```

2. **SSL сертификат**
   ```bash
   # Let's Encrypt
   sudo certbot --nginx -d yourdomain.com
   ```

3. **Мониторинг**
   ```bash
   # Prometheus метрики
   curl http://localhost:8000/metrics
   
   # Логи
   tail -f core-api/backend.log
   ```

## 🔒 Безопасность

### Аутентификация и авторизация

1. **JWT токены**
   ```python
   # Генерация токена
   token = jwt.encode({
       "user_id": user.id,
       "exp": datetime.utcnow() + timedelta(hours=24)
   }, JWT_SECRET, algorithm="HS256")
   ```

2. **Роли пользователей**
   ```python
   class UserRole(Enum):
       ADMIN = "admin"
       MANAGER = "manager"
       OPERATOR = "operator"
       CLIENT = "client"
   ```

3. **Права доступа**
   ```python
   @require_role(UserRole.ADMIN)
   async def admin_endpoint():
       pass
   ```

### Шифрование данных

1. **Шифрование в покое**
   ```python
   # AES шифрование
   from cryptography.fernet import Fernet
   
   cipher = Fernet(ENCRYPTION_KEY)
   encrypted_data = cipher.encrypt(sensitive_data.encode())
   ```

2. **Шифрование в передаче**
   ```python
   # HTTPS обязательно
   # TLS 1.2+ для всех соединений
   ```

### Валидация Click подписи

```python
def validate_click_signature(request_data: dict, secret_key: str) -> bool:
    """Проверка подписи Click webhook"""
    expected_signature = generate_click_signature(request_data, secret_key)
    received_signature = request_data.get('sign_string', '')
    return hmac.compare_digest(expected_signature, received_signature)
```

## 📈 Мониторинг и аналитика

### Метрики системы

1. **Prometheus метрики**
   ```python
   # Счетчики
   payment_counter = Counter('click_payments_total', 'Total Click payments')
   sms_counter = Counter('sms_sent_total', 'Total SMS sent')
   
   # Гистограммы
   response_time = Histogram('api_response_time_seconds', 'API response time')
   ```

2. **Grafana дашборды**
   - Платежи Click в реальном времени
   - SMS статистика
   - Производительность API
   - Статус GSM модулей

### Логирование

1. **Структурированные логи**
   ```python
   import structlog
   
   logger = structlog.get_logger()
   logger.info("Payment processed", 
               payment_id=payment.id,
               amount=payment.amount,
               method="click")
   ```

2. **Централизованное логирование**
   ```bash
   # ELK Stack или аналоги
   # Логи в JSON формате
   ```

## 🧪 Тестирование

### Юнит тесты

```bash
# Запуск всех тестов
cd core-api
python -m pytest tests/ -v

# Тесты Click интеграции
python -m pytest tests/test_click_integration.py -v

# Тесты GSM модулей
python -m pytest tests/test_gsm_modules.py -v
```

### Интеграционные тесты

```bash
# Тест полного платежного потока
python test_click_integration.py

# Тест SMS отправки
python test_sms_integration.py
```

### Нагрузочное тестирование

```bash
# Установка locust
pip install locust

# Запуск нагрузочных тестов
locust -f tests/load_test.py --host=http://localhost:8000
```

## 🤝 Вклад в проект

### Как внести вклад

1. **Форк репозитория**
   ```bash
   git clone https://github.com/yourusername/Call-center-.git
   ```

2. **Создание ветки**
   ```bash
   git checkout -b feature/new-feature
   ```

3. **Внесение изменений**
   ```bash
   git add .
   git commit -m "Add new feature"
   ```

4. **Pull Request**
   ```bash
   git push origin feature/new-feature
   # Создать PR на GitHub
   ```

### Стандарты кода

1. **Python**
   - PEP 8 соответствие
   - Type hints обязательны
   - Docstrings для всех функций

2. **JavaScript**
   - ESLint конфигурация
   - Prettier форматирование
   - JSDoc комментарии

3. **Тестирование**
   - Минимум 80% покрытия
   - Интеграционные тесты
   - Документация API

## 📞 Поддержка

### Контакты

- **GitHub Issues**: [Создать issue](https://github.com/NigoraAsil/Call-center-/issues)
- **Email**: support@voiceconnect.uz
- **Telegram**: @voiceconnect_support
- **Документация**: [docs.voiceconnect.uz](https://docs.voiceconnect.uz)

### FAQ

**Q: Как настроить Click API?**
A: Зарегистрируйтесь на click.uz, получите Service ID и Secret Key, настройте webhook URL.

**Q: Какие GSM модули поддерживаются?**
A: SIM800C, SIM800L, SIM900A и совместимые модули с AT командами.

**Q: Можно ли использовать без Click API?**
A: Да, система работает без платежей, но функции подписок будут недоступны.

**Q: Поддерживается ли мультитенантность?**
A: Да, система поддерживает множественных клиентов с изолированными данными.

## 📋 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🗺️ Дорожная карта

### Q1 2024
- [x] Интеграция Click API
- [x] SIM800C GSM модули
- [x] Многоязычная поддержка
- [x] Автоматический перевод
- [ ] Мобильное приложение

### Q2 2024
- [ ] Голосовые AI ассистенты
- [ ] Расширенная аналитика
- [ ] Интеграция с CRM системами
- [ ] API для третьих сторон

### Q3 2024
- [ ] Машинное обучение для прогнозов
- [ ] Автоматизация маркетинга
- [ ] Интеграция с социальными сетями
- [ ] Расширенная отчетность

---

**VoiceConnect Pro** - Расширение возможностей узбекского бизнеса с помощью интеллектуальных коммуникационных решений.

*Создано с ❤️ для узбекского рынка*