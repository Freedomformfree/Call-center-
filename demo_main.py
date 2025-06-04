#!/usr/bin/env python3
"""
Демонстрационная версия VoiceConnect Pro
Показывает полную логическую цепочку от регистрации до подключения ИИ функций
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn

# Создаем FastAPI приложение
app = FastAPI(
    title="VoiceConnect Pro - Demo",
    description="Демонстрация полной логической цепочки от регистрации до ИИ функций",
    version="1.0.0"
)

# Добавляем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Временное хранилище данных (в реальном проекте - база данных)
demo_data = {
    "registrations": {},
    "users": {},
    "temp_assignments": {},
    "ai_functions": {
        "email_sender": {"name": "Email Отправитель", "active": True},
        "sms_sender": {"name": "SMS Отправитель", "active": True},
        "lead_qualifier": {"name": "Квалификатор лидов", "active": True},
        "payment_processor": {"name": "Обработчик платежей", "active": True},
        "taxi_booking": {"name": "Заказ такси", "active": True},
        "weather_checker": {"name": "Проверка погоды", "active": True},
        "translator": {"name": "Переводчик", "active": True},
        "scheduler": {"name": "Планировщик", "active": True}
    }
}

# Монтируем статические файлы
try:
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
except:
    pass

@app.get("/flow")
async def flow_diagram():
    """Показать диаграмму логической цепочки"""
    return RedirectResponse(url="/static/flow-diagram.html")

@app.get("/")
async def root():
    """Главная страница"""
    return RedirectResponse(url="/static/index.html")

# ==================== ЭТАП 1: РЕГИСТРАЦИЯ КЛИЕНТА ====================

@app.post("/api/v1/registration/start")
async def start_registration(registration_data: dict):
    """
    ЭТАП 1.1: Начало регистрации клиента
    
    Логическая цепочка:
    1. Клиент заполняет форму на frontend/index.html
    2. JavaScript отправляет данные на этот эндпоинт
    3. Система генерирует SMS код
    4. Отправляет SMS через SIM800C модули
    """
    try:
        email = registration_data.get("email")
        password = registration_data.get("password")
        phone = registration_data.get("phone")
        
        if not all([email, password, phone]):
            raise HTTPException(status_code=400, detail="Отсутствуют обязательные поля")
        
        # Генерируем ID регистрации
        registration_id = str(uuid4())
        
        # Генерируем SMS код
        sms_code = "123456"  # В реальности - случайный код
        
        # Сохраняем данные регистрации
        demo_data["registrations"][registration_id] = {
            "email": email,
            "password": password,
            "phone": phone,
            "sms_code": sms_code,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat(),
            "verified": False,
            "attempts": 0
        }
        
        # Симулируем отправку SMS через SIM800C
        print(f"📱 SMS отправлен на {phone}: Код подтверждения: {sms_code}")
        
        return {
            "success": True,
            "registration_id": registration_id,
            "message": "SMS код отправлен на ваш номер",
            "expires_in_minutes": 10,
            "step": "sms_verification"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка регистрации: {str(e)}")

@app.post("/api/v1/registration/verify-sms")
async def verify_sms_code(verification_data: dict):
    """
    ЭТАП 1.2: Верификация SMS кода
    
    Логическая цепочка:
    1. Клиент вводит SMS код в форме
    2. Система проверяет код через SIM800C модули
    3. При успехе создается аккаунт пользователя
    4. Генерируется JWT токен
    """
    try:
        registration_id = verification_data.get("registration_id")
        sms_code = verification_data.get("sms_code")
        
        if not all([registration_id, sms_code]):
            raise HTTPException(status_code=400, detail="Отсутствуют обязательные поля")
        
        # Проверяем регистрацию
        registration = demo_data["registrations"].get(registration_id)
        if not registration:
            raise HTTPException(status_code=404, detail="Регистрация не найдена")
        
        # Проверяем код
        if registration["sms_code"] != sms_code:
            registration["attempts"] += 1
            if registration["attempts"] >= 3:
                raise HTTPException(status_code=429, detail="Превышено количество попыток")
            raise HTTPException(status_code=400, detail="Неверный SMS код")
        
        # Создаем пользователя
        user_id = str(uuid4())
        demo_data["users"][user_id] = {
            "id": user_id,
            "email": registration["email"],
            "phone": registration["phone"],
            "created_at": datetime.now().isoformat(),
            "verified": True,
            "subscription_status": "trial",
            "ai_functions_enabled": False
        }
        
        # Отмечаем регистрацию как завершенную
        registration["verified"] = True
        registration["user_id"] = user_id
        
        print(f"✅ Пользователь {registration['email']} успешно зарегистрирован")
        
        return {
            "success": True,
            "user_id": user_id,
            "message": "Регистрация завершена успешно",
            "step": "temp_phone_assignment"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка верификации: {str(e)}")

# ==================== ЭТАП 2: ВРЕМЕННЫЙ НОМЕР ДЛЯ КОНСУЛЬТАЦИИ ====================

@app.post("/api/v1/consultation/assign-temp-phone")
async def assign_temp_phone(request_data: dict):
    """
    ЭТАП 2.1: Назначение временного номера для консультации
    
    Логическая цепочка:
    1. После регистрации клиенту предлагается консультация
    2. Система назначает временный корпоративный номер на 30 минут
    3. Клиент может позвонить для разговора с ИИ
    """
    try:
        user_id = request_data.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="Отсутствует user_id")
        
        user = demo_data["users"].get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Генерируем временный номер
        temp_phone = "+998901234567"  # В реальности - из пула доступных номеров
        assignment_id = str(uuid4())
        expires_at = datetime.now() + timedelta(minutes=30)
        
        # Сохраняем назначение
        demo_data["temp_assignments"][assignment_id] = {
            "user_id": user_id,
            "phone_number": temp_phone,
            "assigned_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat(),
            "active": True,
            "consultation_completed": False
        }
        
        print(f"📞 Временный номер {temp_phone} назначен пользователю {user['email']} на 30 минут")
        
        return {
            "success": True,
            "temp_phone": temp_phone,
            "expires_at": expires_at.isoformat(),
            "minutes_remaining": 30,
            "message": "Позвоните на этот номер в течение 30 минут для консультации с ИИ",
            "step": "ai_consultation"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка назначения номера: {str(e)}")

# ==================== ЭТАП 3: ИИ КОНСУЛЬТАЦИЯ ====================

@app.post("/api/v1/consultation/simulate-call")
async def simulate_ai_consultation(call_data: dict):
    """
    ЭТАП 3.1: Симуляция звонка и ИИ консультации
    
    Логическая цепочка:
    1. Клиент звонит на временный номер
    2. SIM800C модуль принимает звонок
    3. Голосовой мост (voice-bridge) обрабатывает аудио
    4. Gemini API анализирует речь и отвечает
    5. TTS преобразует ответ в речь
    """
    try:
        user_id = call_data.get("user_id")
        phone_number = call_data.get("phone_number")
        
        if not all([user_id, phone_number]):
            raise HTTPException(status_code=400, detail="Отсутствуют обязательные поля")
        
        # Проверяем назначение
        assignment = None
        for assign_id, assign_data in demo_data["temp_assignments"].items():
            if assign_data["user_id"] == user_id and assign_data["phone_number"] == phone_number:
                assignment = assign_data
                break
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Временное назначение не найдено")
        
        # Симулируем ИИ консультацию
        consultation_result = {
            "call_duration": "5:23",
            "client_needs": [
                "Автоматизация звонков",
                "SMS рассылки",
                "Аналитика продаж",
                "Интеграция с CRM"
            ],
            "recommended_features": [
                "email_sender",
                "sms_sender", 
                "lead_qualifier",
                "payment_processor"
            ],
            "sentiment_score": 0.85,
            "interest_level": "high",
            "budget_range": "$50-100/month",
            "decision_timeline": "within_week"
        }
        
        # Обновляем назначение
        assignment["consultation_completed"] = True
        assignment["consultation_result"] = consultation_result
        
        print(f"🤖 ИИ консультация завершена для пользователя {user_id}")
        print(f"   Потребности: {', '.join(consultation_result['client_needs'])}")
        print(f"   Рекомендованные функции: {', '.join(consultation_result['recommended_features'])}")
        
        return {
            "success": True,
            "consultation_result": consultation_result,
            "message": "Консультация завершена. Готово предложение подписки.",
            "step": "subscription_offer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка консультации: {str(e)}")

# ==================== ЭТАП 4: ПРЕДЛОЖЕНИЕ ПОДПИСКИ ====================

@app.post("/api/v1/subscription/create-offer")
async def create_subscription_offer(offer_data: dict):
    """
    ЭТАП 4.1: Создание персонализированного предложения подписки
    
    Логическая цепочка:
    1. На основе ИИ консультации формируется предложение
    2. Рассчитывается стоимость исходя из потребностей
    3. Предлагается оптимальный план подписки
    """
    try:
        user_id = offer_data.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="Отсутствует user_id")
        
        user = demo_data["users"].get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Находим результат консультации
        consultation_result = None
        for assignment in demo_data["temp_assignments"].values():
            if assignment["user_id"] == user_id and assignment.get("consultation_result"):
                consultation_result = assignment["consultation_result"]
                break
        
        if not consultation_result:
            raise HTTPException(status_code=404, detail="Результат консультации не найден")
        
        # Создаем персонализированное предложение
        recommended_functions = consultation_result["recommended_features"]
        base_price = 20.0
        function_price = len(recommended_functions) * 5.0
        total_price = base_price + function_price
        
        subscription_offer = {
            "plan_name": "VoiceConnect Pro - Персональный",
            "monthly_price": total_price,
            "currency": "USD",
            "included_functions": recommended_functions,
            "features": [
                "Безлимитные звонки и SMS",
                "Множественные SIM800C модули", 
                "Продвинутая ИИ автоматизация",
                "Аналитика в реальном времени",
                "Многоязычная поддержка",
                "24/7 поддержка по email"
            ],
            "trial_period": 14,
            "discount": 20 if consultation_result["interest_level"] == "high" else 0
        }
        
        if subscription_offer["discount"] > 0:
            subscription_offer["discounted_price"] = total_price * (1 - subscription_offer["discount"] / 100)
        
        print(f"💰 Создано предложение подписки для {user['email']}")
        print(f"   План: {subscription_offer['plan_name']}")
        print(f"   Цена: ${subscription_offer['monthly_price']}/месяц")
        print(f"   Функции: {', '.join(recommended_functions)}")
        
        return {
            "success": True,
            "subscription_offer": subscription_offer,
            "message": "Персонализированное предложение готово",
            "step": "payment_processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания предложения: {str(e)}")

# ==================== ЭТАП 5: ОБРАБОТКА ПЛАТЕЖА ====================

@app.post("/api/v1/payment/process-subscription")
async def process_subscription_payment(payment_data: dict):
    """
    ЭТАП 5.1: Обработка платежа за подписку
    
    Логическая цепочка:
    1. Клиент соглашается на подписку
    2. Обработка платежа через Click API (для Узбекистана)
    3. При успешном платеже активируется подписка
    4. Включаются ИИ агентские функции
    """
    try:
        user_id = payment_data.get("user_id")
        payment_method = payment_data.get("payment_method", "click")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="Отсутствует user_id")
        
        user = demo_data["users"].get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Симулируем обработку платежа через Click API
        payment_result = {
            "transaction_id": f"click_{uuid4().hex[:12]}",
            "status": "completed",
            "amount": payment_data.get("amount", 20.0),
            "currency": "USD",
            "payment_method": payment_method,
            "processed_at": datetime.now().isoformat()
        }
        
        # Активируем подписку
        user["subscription_status"] = "active"
        user["subscription_started_at"] = datetime.now().isoformat()
        user["subscription_expires_at"] = (datetime.now() + timedelta(days=30)).isoformat()
        user["ai_functions_enabled"] = True
        user["payment_info"] = payment_result
        
        print(f"💳 Платеж обработан для {user['email']}")
        print(f"   Транзакция: {payment_result['transaction_id']}")
        print(f"   Сумма: ${payment_result['amount']}")
        print(f"   Подписка активна до: {user['subscription_expires_at']}")
        
        return {
            "success": True,
            "payment_result": payment_result,
            "subscription_status": "active",
            "message": "Платеж успешно обработан. Подписка активирована.",
            "step": "ai_functions_activation"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки платежа: {str(e)}")

# ==================== ЭТАП 6: АКТИВАЦИЯ ИИ ФУНКЦИЙ ====================

@app.post("/api/v1/ai-functions/activate")
async def activate_ai_functions(activation_data: dict):
    """
    ЭТАП 6.1: Активация ИИ агентских функций
    
    Логическая цепочка:
    1. После успешного платежа активируются ИИ функции
    2. Пользователь получает доступ к панели управления
    3. Можно настраивать и запускать агентские функции
    """
    try:
        user_id = activation_data.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="Отсутствует user_id")
        
        user = demo_data["users"].get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        if not user.get("ai_functions_enabled"):
            raise HTTPException(status_code=403, detail="ИИ функции не активированы")
        
        # Получаем рекомендованные функции из консультации
        recommended_functions = []
        for assignment in demo_data["temp_assignments"].values():
            if assignment["user_id"] == user_id and assignment.get("consultation_result"):
                recommended_functions = assignment["consultation_result"]["recommended_features"]
                break
        
        # Активируем функции
        activated_functions = {}
        for func_id in recommended_functions:
            if func_id in demo_data["ai_functions"]:
                activated_functions[func_id] = {
                    **demo_data["ai_functions"][func_id],
                    "activated_at": datetime.now().isoformat(),
                    "usage_count": 0
                }
        
        user["activated_functions"] = activated_functions
        
        print(f"🤖 ИИ функции активированы для {user['email']}")
        print(f"   Активированные функции: {', '.join(activated_functions.keys())}")
        
        return {
            "success": True,
            "activated_functions": activated_functions,
            "dashboard_url": "/dashboard",
            "message": "ИИ функции успешно активированы. Добро пожаловать в VoiceConnect Pro!",
            "step": "complete"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка активации функций: {str(e)}")

# ==================== ЭТАП 7: ИСПОЛЬЗОВАНИЕ ИИ ФУНКЦИЙ ====================

@app.post("/api/v1/ai-functions/execute")
async def execute_ai_function(execution_data: dict):
    """
    ЭТАП 7.1: Выполнение ИИ агентской функции
    
    Логическая цепочка:
    1. Пользователь выбирает функцию в панели управления
    2. Настраивает параметры выполнения
    3. Функция выполняется с использованием соответствующих API
    4. Результат возвращается пользователю
    """
    try:
        user_id = execution_data.get("user_id")
        function_id = execution_data.get("function_id")
        parameters = execution_data.get("parameters", {})
        
        if not all([user_id, function_id]):
            raise HTTPException(status_code=400, detail="Отсутствуют обязательные поля")
        
        user = demo_data["users"].get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        if not user.get("ai_functions_enabled"):
            raise HTTPException(status_code=403, detail="ИИ функции не активированы")
        
        activated_functions = user.get("activated_functions", {})
        if function_id not in activated_functions:
            raise HTTPException(status_code=403, detail="Функция не активирована")
        
        # Симулируем выполнение различных функций
        execution_results = {
            "email_sender": {
                "emails_sent": parameters.get("recipient_count", 1),
                "delivery_rate": "98%",
                "open_rate": "24%"
            },
            "sms_sender": {
                "sms_sent": parameters.get("recipient_count", 1),
                "delivery_rate": "99%",
                "response_rate": "12%"
            },
            "lead_qualifier": {
                "leads_processed": parameters.get("lead_count", 10),
                "qualified_leads": 7,
                "qualification_rate": "70%"
            },
            "payment_processor": {
                "payments_processed": parameters.get("payment_count", 1),
                "success_rate": "95%",
                "total_amount": "$1,250"
            }
        }
        
        result = execution_results.get(function_id, {"status": "executed", "message": "Функция выполнена"})
        
        # Обновляем счетчик использования
        activated_functions[function_id]["usage_count"] += 1
        activated_functions[function_id]["last_used"] = datetime.now().isoformat()
        
        print(f"⚡ Выполнена функция {function_id} для пользователя {user['email']}")
        print(f"   Результат: {result}")
        
        return {
            "success": True,
            "function_id": function_id,
            "execution_result": result,
            "executed_at": datetime.now().isoformat(),
            "message": f"Функция {demo_data['ai_functions'][function_id]['name']} успешно выполнена"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения функции: {str(e)}")

# ==================== ИНФОРМАЦИОННЫЕ ЭНДПОИНТЫ ====================

@app.get("/api/v1/user/{user_id}/status")
async def get_user_status(user_id: str):
    """Получить статус пользователя и его прогресс"""
    user = demo_data["users"].get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return {
        "user": user,
        "current_step": "complete" if user.get("ai_functions_enabled") else "registration"
    }

@app.get("/api/v1/ai-functions/available")
async def get_available_functions():
    """Получить список доступных ИИ функций"""
    return {
        "functions": demo_data["ai_functions"],
        "total": len(demo_data["ai_functions"])
    }

@app.get("/api/v1/demo/full-flow")
async def get_full_flow_demo():
    """
    Получить полную схему логической цепочки
    """
    flow_steps = [
        {
            "step": 1,
            "name": "Регистрация клиента",
            "description": "Клиент заполняет форму регистрации на сайте",
            "endpoints": ["/api/v1/registration/start"],
            "files": ["frontend/index.html", "core-api/client_registration_service.py"],
            "details": [
                "Клиент вводит email, пароль и номер телефона",
                "Система генерирует SMS код верификации",
                "Код отправляется через SIM800C модули"
            ]
        },
        {
            "step": 2,
            "name": "SMS верификация",
            "description": "Подтверждение номера телефона через SMS",
            "endpoints": ["/api/v1/registration/verify-sms"],
            "files": ["core-api/local_gsm_sms_service.py", "hardware/sim800c_manager.py"],
            "details": [
                "Клиент вводит полученный SMS код",
                "Система проверяет код через SIM800C",
                "При успехе создается аккаунт пользователя"
            ]
        },
        {
            "step": 3,
            "name": "Назначение временного номера",
            "description": "Выделение корпоративного номера для консультации",
            "endpoints": ["/api/v1/consultation/assign-temp-phone"],
            "files": ["core-api/modem_management_service.py"],
            "details": [
                "Система находит свободный корпоративный номер",
                "Назначает его пользователю на 30 минут",
                "Клиент может позвонить для консультации"
            ]
        },
        {
            "step": 4,
            "name": "ИИ консультация",
            "description": "Разговор с ИИ ассистентом через телефон",
            "endpoints": ["/api/v1/consultation/simulate-call"],
            "files": ["voice-bridge/main.py", "voice-bridge/gemini_client.py", "voice-bridge/tts_engine.py"],
            "details": [
                "Клиент звонит на временный номер",
                "SIM800C принимает звонок",
                "Голосовой мост обрабатывает аудио",
                "Gemini API анализирует речь и отвечает",
                "TTS преобразует ответ в речь"
            ]
        },
        {
            "step": 5,
            "name": "Анализ потребностей",
            "description": "ИИ анализирует потребности клиента",
            "endpoints": [],
            "files": ["core-api/agentic_function_service.py"],
            "details": [
                "ИИ определяет потребности клиента",
                "Анализирует тональность разговора",
                "Оценивает уровень заинтересованности",
                "Формирует рекомендации по функциям"
            ]
        },
        {
            "step": 6,
            "name": "Персонализированное предложение",
            "description": "Создание индивидуального плана подписки",
            "endpoints": ["/api/v1/subscription/create-offer"],
            "files": ["core-api/revenue_engine.py"],
            "details": [
                "На основе консультации формируется предложение",
                "Рассчитывается стоимость под потребности",
                "Предлагается оптимальный набор функций"
            ]
        },
        {
            "step": 7,
            "name": "Обработка платежа",
            "description": "Оплата подписки через Click API",
            "endpoints": ["/api/v1/payment/process-subscription"],
            "files": ["core-api/click_payment_service.py", "core-api/click_endpoints.py"],
            "details": [
                "Клиент выбирает способ оплаты",
                "Обработка через Click API (Узбекистан)",
                "Подтверждение платежа через webhook",
                "Активация подписки"
            ]
        },
        {
            "step": 8,
            "name": "Активация ИИ функций",
            "description": "Включение агентских функций для пользователя",
            "endpoints": ["/api/v1/ai-functions/activate"],
            "files": ["core-api/universal_agentic_functions.py", "core-api/business_agentic_functions.py"],
            "details": [
                "Активируются рекомендованные функции",
                "Пользователь получает доступ к панели",
                "Настройка и запуск автоматизации"
            ]
        },
        {
            "step": 9,
            "name": "Использование ИИ функций",
            "description": "Работа с агентскими функциями",
            "endpoints": ["/api/v1/ai-functions/execute"],
            "files": ["core-api/comprehensive_agentic_service.py", "core-api/ai_tools_service.py"],
            "details": [
                "Email рассылки через SendGrid",
                "SMS через SIM800C модули",
                "Квалификация лидов",
                "Обработка платежей",
                "Заказ такси через Yandex API",
                "Переводы через Google Translate",
                "Планирование встреч",
                "Аналитика и отчеты"
            ]
        }
    ]
    
    return {
        "title": "VoiceConnect Pro - Полная логическая цепочка",
        "description": "От регистрации клиента до использования ИИ агентских функций",
        "total_steps": len(flow_steps),
        "flow_steps": flow_steps,
        "key_technologies": [
            "FastAPI (Python) - Backend API",
            "SIM800C GSM модули - SMS/Голосовые вызовы",
            "Gemini API - ИИ обработка речи",
            "Click API - Платежная система Узбекистана",
            "PostgreSQL - База данных",
            "Redis - Кэширование",
            "WebRTC - Голосовые вызовы в браузере",
            "TTS/STT - Преобразование речи",
            "SendGrid - Email рассылки",
            "Yandex APIs - Интеграции сервисов"
        ],
        "architecture_components": [
            "core-api - Основная бизнес-логика",
            "voice-bridge - Обработка голосовых вызовов",
            "modem-daemon - Управление SIM800C модулями",
            "task-runner - Фоновые задачи и ML",
            "frontend - Веб-интерфейс",
            "dashboard - Панель управления"
        ]
    }

# Запуск демо-сервера
if __name__ == "__main__":
    print("🚀 Запуск демонстрации VoiceConnect Pro")
    print("📋 Полная логическая цепочка от регистрации до ИИ функций")
    print("🌐 Доступно по адресу: https://work-1-mdgxngtqgweewuld.prod-runtime.all-hands.dev")
    print("📖 API документация: https://work-1-mdgxngtqgweewuld.prod-runtime.all-hands.dev/docs")
    print("🔄 Полная схема: https://work-1-mdgxngtqgweewuld.prod-runtime.all-hands.dev/api/v1/demo/full-flow")
    
    uvicorn.run(
        "demo_main:app",
        host="0.0.0.0",
        port=12000,
        reload=True,
        access_log=True
    )