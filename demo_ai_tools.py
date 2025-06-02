#!/usr/bin/env python3
"""
Демонстрация работы AI инструментов в системе
"""

import asyncio
import json
import requests
from datetime import datetime

# Базовый URL API
BASE_URL = "http://localhost:12000/api/v1"

def print_section(title):
    """Печать заголовка секции"""
    print(f"\n{'='*60}")
    print(f"🤖 {title}")
    print(f"{'='*60}")

def print_tool_info(tool_name, tool_data):
    """Печать информации об инструменте"""
    print(f"\n📱 {tool_data['name']}")
    print(f"   📝 Описание: {tool_data['description']}")
    print(f"   🔧 Требуется настройка: {', '.join(tool_data['setup_required'])}")
    if 'scopes' in tool_data:
        print(f"   🔐 Разрешения: {', '.join(tool_data['scopes'])}")

def demonstrate_ai_tools():
    """Демонстрация AI инструментов"""
    
    print_section("ДЕМОНСТРАЦИЯ AI ИНСТРУМЕНТОВ")
    
    # 1. Получение списка доступных инструментов
    print_section("1. ДОСТУПНЫЕ AI ИНСТРУМЕНТЫ")
    
    try:
        response = requests.get(f"{BASE_URL}/client/ai-tools/available")
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                tools = data["tools"]
                print(f"Всего доступно инструментов: {data['total_count']}")
                
                for tool_name, tool_data in tools.items():
                    print_tool_info(tool_name, tool_data)
            else:
                print("❌ Ошибка получения инструментов")
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    
    # 2. Демонстрация возможностей каждого инструмента
    print_section("2. ВОЗМОЖНОСТИ AI ИНСТРУМЕНТОВ")
    
    ai_capabilities = {
        "gmail": {
            "actions": ["send_email", "read_emails", "search_emails", "create_draft"],
            "use_cases": [
                "Автоматическая отправка email клиентам",
                "Чтение и анализ входящих писем", 
                "Поиск писем по ключевым словам",
                "Создание черновиков ответов"
            ]
        },
        "calendar": {
            "actions": ["create_event", "update_event", "delete_event", "get_events"],
            "use_cases": [
                "Автоматическое планирование встреч",
                "Напоминания о важных событиях",
                "Синхронизация календарей",
                "Управление расписанием команды"
            ]
        },
        "drive": {
            "actions": ["upload_file", "download_file", "share_file", "create_folder"],
            "use_cases": [
                "Автоматическое сохранение документов",
                "Обмен файлами с клиентами",
                "Резервное копирование данных",
                "Совместная работа над документами"
            ]
        },
        "slack": {
            "actions": ["send_message", "create_channel", "invite_users", "get_messages"],
            "use_cases": [
                "Уведомления команды о важных событиях",
                "Автоматические отчеты в каналы",
                "Интеграция с рабочими процессами",
                "Мониторинг активности команды"
            ]
        },
        "whatsapp": {
            "actions": ["send_message", "send_media", "get_messages", "create_group"],
            "use_cases": [
                "Массовая рассылка клиентам",
                "Поддержка клиентов через WhatsApp",
                "Отправка уведомлений и напоминаний",
                "Автоматические ответы на запросы"
            ]
        },
        "telegram": {
            "actions": ["send_message", "send_photo", "create_bot", "manage_channels"],
            "use_cases": [
                "Уведомления через Telegram бота",
                "Автоматические отчеты в каналы",
                "Интерактивные опросы и голосования",
                "Мониторинг системы через бота"
            ]
        },
        "zoom": {
            "actions": ["create_meeting", "schedule_meeting", "get_recordings", "manage_participants"],
            "use_cases": [
                "Автоматическое создание встреч",
                "Планирование регулярных совещаний",
                "Управление участниками",
                "Анализ записей встреч"
            ]
        },
        "stripe": {
            "actions": ["create_payment", "process_refund", "manage_subscriptions", "get_analytics"],
            "use_cases": [
                "Автоматическая обработка платежей",
                "Управление подписками клиентов",
                "Возвраты и компенсации",
                "Финансовая аналитика"
            ]
        },
        "trello": {
            "actions": ["create_card", "update_board", "assign_members", "track_progress"],
            "use_cases": [
                "Автоматическое создание задач",
                "Отслеживание прогресса проектов",
                "Управление командными досками",
                "Интеграция с другими системами"
            ]
        },
        "microsoft": {
            "actions": ["access_outlook", "manage_teams", "onedrive_sync", "sharepoint_integration"],
            "use_cases": [
                "Интеграция с Office 365",
                "Управление Teams каналами",
                "Синхронизация OneDrive",
                "Работа с SharePoint"
            ]
        },
        "hubspot": {
            "actions": ["manage_contacts", "track_deals", "create_reports", "automate_workflows"],
            "use_cases": [
                "Автоматическое управление контактами",
                "Отслеживание сделок",
                "CRM аналитика и отчеты",
                "Автоматизация продаж"
            ]
        },
        "salesforce": {
            "actions": ["manage_leads", "update_opportunities", "create_reports", "workflow_automation"],
            "use_cases": [
                "Управление лидами и возможностями",
                "Автоматизация процессов продаж",
                "Аналитика и прогнозирование",
                "Интеграция с другими системами"
            ]
        }
    }
    
    for tool_name, capabilities in ai_capabilities.items():
        print(f"\n🔧 {tool_name.upper()}")
        print(f"   📋 Доступные действия: {', '.join(capabilities['actions'])}")
        print(f"   💡 Примеры использования:")
        for use_case in capabilities['use_cases']:
            print(f"      • {use_case}")
    
    # 3. Демонстрация интеграции с звонками
    print_section("3. ИНТЕГРАЦИЯ AI ИНСТРУМЕНТОВ С ЗВОНКАМИ")
    
    call_scenarios = [
        {
            "scenario": "Клиент звонит с вопросом о заказе",
            "ai_actions": [
                "🔍 Поиск информации о заказе в CRM (Salesforce/HubSpot)",
                "📧 Отправка подтверждения на email (Gmail)",
                "📅 Планирование звонка для уточнений (Calendar)",
                "💬 Уведомление команды поддержки (Slack/Teams)"
            ]
        },
        {
            "scenario": "Запрос на техническую поддержку",
            "ai_actions": [
                "📋 Создание тикета в системе (Trello)",
                "📁 Загрузка логов в облако (Drive/OneDrive)",
                "👥 Назначение специалиста (Teams/Slack)",
                "📱 Отправка инструкций клиенту (WhatsApp/Telegram)"
            ]
        },
        {
            "scenario": "Оформление подписки",
            "ai_actions": [
                "💳 Обработка платежа (Stripe)",
                "👤 Создание профиля клиента (CRM)",
                "📧 Отправка приветственного письма (Gmail)",
                "🎥 Планирование онбординг встречи (Zoom)"
            ]
        },
        {
            "scenario": "Жалоба клиента",
            "ai_actions": [
                "📝 Фиксация жалобы в CRM",
                "⚡ Эскалация менеджеру (Slack)",
                "📞 Планирование обратного звонка (Calendar)",
                "📊 Анализ истории взаимодействий (Analytics)"
            ]
        }
    ]
    
    for i, scenario in enumerate(call_scenarios, 1):
        print(f"\n{i}. {scenario['scenario']}")
        print("   AI автоматически выполняет:")
        for action in scenario['ai_actions']:
            print(f"      {action}")
    
    # 4. Демонстрация настройки инструментов
    print_section("4. НАСТРОЙКА AI ИНСТРУМЕНТОВ")
    
    config_examples = {
        "Gmail": {
            "client_id": "your-google-client-id",
            "client_secret": "your-google-client-secret", 
            "refresh_token": "your-refresh-token"
        },
        "Slack": {
            "bot_token": "xoxb-your-bot-token",
            "app_token": "xapp-your-app-token"
        },
        "Stripe": {
            "secret_key": "sk_test_your-secret-key",
            "publishable_key": "pk_test_your-publishable-key"
        },
        "WhatsApp": {
            "phone_number_id": "your-phone-number-id",
            "access_token": "your-whatsapp-access-token"
        }
    }
    
    print("Примеры конфигурации:")
    for tool, config in config_examples.items():
        print(f"\n🔧 {tool}:")
        for key, value in config.items():
            print(f"   {key}: {value}")
    
    # 5. Статистика и мониторинг
    print_section("5. МОНИТОРИНГ AI ИНСТРУМЕНТОВ")
    
    monitoring_metrics = [
        "📊 Количество выполненных действий",
        "⏱️ Среднее время отклика API",
        "✅ Процент успешных операций", 
        "💰 Использование API квот",
        "🔄 Частота использования инструментов",
        "⚠️ Ошибки и их типы",
        "📈 Тренды использования",
        "🎯 Эффективность автоматизации"
    ]
    
    print("Система отслеживает:")
    for metric in monitoring_metrics:
        print(f"   {metric}")
    
    print_section("ЗАКЛЮЧЕНИЕ")
    print("""
🎯 AI инструменты обеспечивают:
   • Автоматизацию рутинных задач
   • Интеграцию с популярными сервисами
   • Повышение эффективности работы
   • Улучшение качества обслуживания клиентов
   • Снижение времени обработки запросов
   • Централизованное управление процессами

🚀 Система готова к работе с реальными API!
""")

if __name__ == "__main__":
    demonstrate_ai_tools()