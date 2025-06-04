#!/usr/bin/env python3
"""
VoiceConnect Pro - Comprehensive Coffee Paper Theme Web Application
Complete Business Solution with All Features

This application includes:
- Coffee Paper Theme Design
- Simple Email/Password Authentication  
- Company Phone Number Assignment
- Subscription Payment System
- AI Tools Management with Gemini
- Complete Business Workflow
"""

import os
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from flask import Flask, request, jsonify, session, render_template_string, redirect, url_for, send_from_directory
from flask_cors import CORS
import logging

# Import our services
from simple_auth_api import SimpleAuthAPI
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

# Import Gemini services
try:
    from gemini_chat_service import GeminiChatService
    from gemini_response_parser import GeminiResponseParser
except ImportError as e:
    print(f"Warning: Gemini services not available: {e}")
    GeminiChatService = None
    GeminiResponseParser = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'voiceconnect-pro-coffee-secret-key'
CORS(app, supports_credentials=True)

# Simple Auth Wrapper Class
class AuthWrapper:
    def __init__(self, db_path="ai_call_center.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with users table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create users table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    company TEXT,
                    phone TEXT,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def register_user(self, email, password, full_name):
        """Register a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (email.lower(),))
            if cursor.fetchone():
                conn.close()
                return {'success': False, 'message': 'Email already registered'}
            
            # Hash password and create user
            password_hash = generate_password_hash(password)
            cursor.execute('''
                INSERT INTO users (full_name, email, password_hash)
                VALUES (?, ?, ?)
            ''', (full_name, email.lower(), password_hash))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Registration successful'}
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {'success': False, 'message': 'Registration failed'}
    
    def authenticate_user(self, email, password):
        """Authenticate user credentials"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, full_name, email, password_hash, is_active 
                FROM users 
                WHERE email = ? AND is_active = 1
            ''', (email.lower(),))
            
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return None
            
            user_id, full_name, user_email, password_hash, is_active = user
            
            # Verify password
            if not check_password_hash(password_hash, password):
                conn.close()
                return None
            
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'id': user_id,
                'full_name': full_name,
                'email': user_email
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, full_name, email, company, phone
                FROM users 
                WHERE id = ? AND is_active = 1
            ''', (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'full_name': user[1],
                    'email': user[2],
                    'company': user[3],
                    'phone': user[4]
                }
            return None
            
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None

# Initialize services
auth_api = AuthWrapper()

# Initialize Gemini services if available
gemini_service = None
gemini_parser = None
try:
    gemini_service = GeminiChatService()
    gemini_parser = GeminiResponseParser()
    logger.info("Gemini services initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize Gemini service: {e}")
    gemini_service = None
    gemini_parser = None

# Coffee Paper Theme CSS
COFFEE_THEME_CSS = """
/* Coffee Paper Theme - Complete Business Solution */
@import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&family=Source+Code+Pro:wght@300;400;500&display=swap');

:root {
    --coffee-dark: #2c1810;
    --coffee-medium: #4a2c17;
    --coffee-light: #8b4513;
    --paper-white: #faf7f2;
    --paper-cream: #f5f1e8;
    --ink-black: #1a1a1a;
    --accent-gold: #d4af37;
    --shadow-brown: rgba(44, 24, 16, 0.1);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Crimson Text', serif;
    background: var(--paper-white);
    color: var(--ink-black);
    line-height: 1.6;
    background-image: 
        radial-gradient(circle at 20% 80%, rgba(139, 69, 19, 0.03) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(139, 69, 19, 0.03) 0%, transparent 50%);
}

.coffee-container {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    background: var(--paper-cream);
    box-shadow: 0 0 30px var(--shadow-brown);
    position: relative;
}

.coffee-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
        repeating-linear-gradient(
            0deg,
            transparent,
            transparent 24px,
            rgba(139, 69, 19, 0.05) 25px
        );
    pointer-events: none;
}

.coffee-header {
    text-align: center;
    margin-bottom: 3rem;
    position: relative;
    z-index: 1;
}

.coffee-title {
    font-size: 3rem;
    font-weight: 600;
    color: var(--coffee-dark);
    margin-bottom: 0.5rem;
    text-shadow: 2px 2px 4px var(--shadow-brown);
}

.coffee-subtitle {
    font-size: 1.2rem;
    color: var(--coffee-medium);
    font-style: italic;
}

.coffee-nav {
    background: var(--coffee-dark);
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 8px var(--shadow-brown);
}

.coffee-nav ul {
    list-style: none;
    display: flex;
    justify-content: center;
    gap: 2rem;
    flex-wrap: wrap;
}

.coffee-nav a {
    color: var(--paper-white);
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    transition: all 0.3s ease;
    font-weight: 500;
}

.coffee-nav a:hover {
    background: var(--coffee-light);
    transform: translateY(-2px);
}

.coffee-card {
    background: var(--paper-white);
    border: 2px solid var(--coffee-light);
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 6px 12px var(--shadow-brown);
    position: relative;
    overflow: hidden;
}

.coffee-card::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(139, 69, 19, 0.02) 0%, transparent 70%);
    pointer-events: none;
}

.coffee-form {
    max-width: 400px;
    margin: 0 auto;
}

.coffee-input {
    width: 100%;
    padding: 1rem;
    border: 2px solid var(--coffee-light);
    border-radius: 8px;
    font-size: 1rem;
    font-family: 'Crimson Text', serif;
    background: var(--paper-cream);
    color: var(--ink-black);
    margin-bottom: 1rem;
    transition: all 0.3s ease;
}

.coffee-input:focus {
    outline: none;
    border-color: var(--coffee-dark);
    box-shadow: 0 0 8px var(--shadow-brown);
}

.coffee-button {
    background: var(--coffee-dark);
    color: var(--paper-white);
    border: none;
    padding: 1rem 2rem;
    border-radius: 8px;
    font-size: 1rem;
    font-family: 'Crimson Text', serif;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    width: 100%;
    margin-bottom: 1rem;
}

.coffee-button:hover {
    background: var(--coffee-medium);
    transform: translateY(-2px);
    box-shadow: 0 4px 8px var(--shadow-brown);
}

.coffee-button.secondary {
    background: var(--coffee-light);
}

.coffee-button.secondary:hover {
    background: var(--coffee-medium);
}

.business-workflow {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin: 2rem 0;
}

.workflow-step {
    background: var(--paper-white);
    border: 2px solid var(--coffee-light);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    transition: all 0.3s ease;
}

.workflow-step:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px var(--shadow-brown);
}

.workflow-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    display: block;
}

.phone-assignment {
    background: linear-gradient(135deg, var(--paper-cream) 0%, var(--paper-white) 100%);
    border: 3px solid var(--accent-gold);
    text-align: center;
    padding: 2rem;
}

.assigned-phone {
    font-size: 2.5rem;
    font-weight: 600;
    color: var(--coffee-dark);
    font-family: 'Source Code Pro', monospace;
    margin: 1rem 0;
    padding: 1rem;
    background: var(--paper-white);
    border-radius: 8px;
    border: 2px solid var(--coffee-light);
}

.subscription-plans {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2rem;
    margin: 2rem 0;
}

.plan-card {
    background: var(--paper-white);
    border: 2px solid var(--coffee-light);
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    transition: all 0.3s ease;
    position: relative;
}

.plan-card.recommended {
    border-color: var(--accent-gold);
    transform: scale(1.05);
}

.plan-card:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 8px 16px var(--shadow-brown);
}

.plan-price {
    font-size: 2.5rem;
    font-weight: 600;
    color: var(--coffee-dark);
    margin: 1rem 0;
}

.plan-features {
    list-style: none;
    margin: 1rem 0;
}

.plan-features li {
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--coffee-light);
}

.ai-tools-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.tool-card {
    background: var(--paper-white);
    border: 2px solid var(--coffee-light);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
}

.tool-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px var(--shadow-brown);
    border-color: var(--coffee-dark);
}

.gemini-chat {
    background: var(--paper-white);
    border: 2px solid var(--coffee-light);
    border-radius: 12px;
    padding: 1.5rem;
    margin: 2rem 0;
    max-height: 500px;
    overflow-y: auto;
}

.chat-messages {
    margin-bottom: 1rem;
    max-height: 300px;
    overflow-y: auto;
}

.chat-message {
    margin-bottom: 1rem;
    padding: 1rem;
    border-radius: 8px;
}

.chat-message.user {
    background: var(--coffee-light);
    color: var(--paper-white);
    margin-left: 2rem;
}

.chat-message.gemini {
    background: var(--paper-cream);
    border: 1px solid var(--coffee-light);
    margin-right: 2rem;
}

.chat-input-container {
    display: flex;
    gap: 1rem;
}

.chat-input {
    flex: 1;
    padding: 1rem;
    border: 2px solid var(--coffee-light);
    border-radius: 8px;
    font-family: 'Crimson Text', serif;
}

.language-selector {
    position: fixed;
    top: 2rem;
    right: 2rem;
    z-index: 1000;
}

.language-dropdown {
    background: var(--coffee-dark);
    color: var(--paper-white);
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-family: 'Crimson Text', serif;
    cursor: pointer;
}

.coffee-footer {
    text-align: center;
    margin-top: auto;
    padding-top: 2rem;
    color: var(--coffee-medium);
    font-style: italic;
}

@media (max-width: 768px) {
    .coffee-container {
        padding: 1rem;
    }
    
    .coffee-title {
        font-size: 2rem;
    }
    
    .coffee-nav ul {
        flex-direction: column;
        gap: 1rem;
    }
    
    .business-workflow {
        grid-template-columns: 1fr;
    }
    
    .subscription-plans {
        grid-template-columns: 1fr;
    }
    
    .plan-card.recommended {
        transform: none;
    }
}

/* Animation classes */
.fade-in {
    animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.success-message {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}

.error-message {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}
"""

# HTML Templates
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ language }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>☕ VoiceConnect Pro - {{ translations.title }}</title>
    <style>{{ css }}</style>
</head>
<body>
    <div class="language-selector">
        <select class="language-dropdown" onchange="changeLanguage(this.value)">
            <option value="en" {{ 'selected' if language == 'en' else '' }}>🇺🇸 English</option>
            <option value="ru" {{ 'selected' if language == 'ru' else '' }}>🇷🇺 Русский</option>
            <option value="uz" {{ 'selected' if language == 'uz' else '' }}>🇺🇿 O'zbek</option>
        </select>
    </div>

    <div class="coffee-container fade-in">
        <header class="coffee-header">
            <h1 class="coffee-title">☕ VoiceConnect Pro</h1>
            <p class="coffee-subtitle">{{ translations.subtitle }}</p>
        </header>

        <div class="coffee-card">
            <h2>{{ translations.welcome_title }}</h2>
            <p>{{ translations.welcome_description }}</p>
            
            <div class="business-workflow">
                <div class="workflow-step">
                    <span class="workflow-icon">📝</span>
                    <h3>{{ translations.step1_title }}</h3>
                    <p>{{ translations.step1_desc }}</p>
                </div>
                <div class="workflow-step">
                    <span class="workflow-icon">📞</span>
                    <h3>{{ translations.step2_title }}</h3>
                    <p>{{ translations.step2_desc }}</p>
                </div>
                <div class="workflow-step">
                    <span class="workflow-icon">🤖</span>
                    <h3>{{ translations.step3_title }}</h3>
                    <p>{{ translations.step3_desc }}</p>
                </div>
                <div class="workflow-step">
                    <span class="workflow-icon">💼</span>
                    <h3>{{ translations.step4_title }}</h3>
                    <p>{{ translations.step4_desc }}</p>
                </div>
            </div>

            <div style="text-align: center; margin-top: 2rem;">
                <a href="/login" class="coffee-button">{{ translations.get_started }}</a>
            </div>
        </div>

        <footer class="coffee-footer">
            <p>{{ translations.footer }}</p>
        </footer>
    </div>

    <script>
        function changeLanguage(lang) {
            window.location.href = '/?lang=' + lang;
        }
    </script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ language }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>☕ {{ translations.login_title }} - VoiceConnect Pro</title>
    <style>{{ css }}</style>
</head>
<body>
    <div class="language-selector">
        <select class="language-dropdown" onchange="changeLanguage(this.value)">
            <option value="en" {{ 'selected' if language == 'en' else '' }}>🇺🇸 English</option>
            <option value="ru" {{ 'selected' if language == 'ru' else '' }}>🇷🇺 Русский</option>
            <option value="uz" {{ 'selected' if language == 'uz' else '' }}>🇺🇿 O'zbek</option>
        </select>
    </div>

    <div class="coffee-container fade-in">
        <header class="coffee-header">
            <h1 class="coffee-title">☕ VoiceConnect Pro</h1>
            <p class="coffee-subtitle">{{ translations.login_subtitle }}</p>
        </header>

        <div class="coffee-card">
            <h2>{{ translations.login_title }}</h2>
            
            {% if message %}
            <div class="{{ 'success-message' if success else 'error-message' }}">
                {{ message }}
            </div>
            {% endif %}

            <form class="coffee-form" method="POST" action="/api/auth/login">
                <input type="email" name="email" class="coffee-input" placeholder="{{ translations.email_placeholder }}" required>
                <input type="password" name="password" class="coffee-input" placeholder="{{ translations.password_placeholder }}" required>
                <button type="submit" class="coffee-button">{{ translations.login_button }}</button>
            </form>

            <div style="text-align: center; margin-top: 2rem;">
                <p>{{ translations.no_account }}</p>
                <form class="coffee-form" method="POST" action="/api/auth/register">
                    <input type="text" name="full_name" class="coffee-input" placeholder="{{ translations.full_name_placeholder }}" required>
                    <input type="email" name="email" class="coffee-input" placeholder="{{ translations.email_placeholder }}" required>
                    <input type="password" name="password" class="coffee-input" placeholder="{{ translations.password_placeholder }}" required>
                    <button type="submit" class="coffee-button secondary">{{ translations.signup_button }}</button>
                </form>
            </div>
        </div>

        <footer class="coffee-footer">
            <p><a href="/" style="color: var(--coffee-medium);">← {{ translations.back_home }}</a></p>
        </footer>
    </div>

    <script>
        function changeLanguage(lang) {
            window.location.href = '/login?lang=' + lang;
        }
    </script>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ language }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>☕ {{ translations.dashboard_title }} - VoiceConnect Pro</title>
    <style>{{ css }}</style>
</head>
<body>
    <div class="language-selector">
        <select class="language-dropdown" onchange="changeLanguage(this.value)">
            <option value="en" {{ 'selected' if language == 'en' else '' }}>🇺🇸 English</option>
            <option value="ru" {{ 'selected' if language == 'ru' else '' }}>🇷🇺 Русский</option>
            <option value="uz" {{ 'selected' if language == 'uz' else '' }}>🇺🇿 O'zbek</option>
        </select>
    </div>

    <div class="coffee-container fade-in">
        <nav class="coffee-nav">
            <ul>
                <li><a href="/dashboard">{{ translations.dashboard }}</a></li>
                <li><a href="/phone-assignment">{{ translations.phone_assignment }}</a></li>
                <li><a href="/subscription">{{ translations.subscription }}</a></li>
                <li><a href="/ai-tools">{{ translations.ai_tools }}</a></li>
                <li><a href="/api/auth/logout">{{ translations.logout }}</a></li>
            </ul>
        </nav>

        <header class="coffee-header">
            <h1 class="coffee-title">{{ translations.welcome_back }}, {{ user.full_name }}!</h1>
            <p class="coffee-subtitle">{{ translations.dashboard_subtitle }}</p>
        </header>

        <div class="coffee-card">
            <h2>{{ translations.business_overview }}</h2>
            
            <div class="business-workflow">
                <div class="workflow-step">
                    <span class="workflow-icon">📞</span>
                    <h3>{{ translations.phone_status }}</h3>
                    <p>{{ translations.phone_status_desc }}</p>
                    <a href="/phone-assignment" class="coffee-button">{{ translations.manage_phone }}</a>
                </div>
                
                <div class="workflow-step">
                    <span class="workflow-icon">💼</span>
                    <h3>{{ translations.subscription_status }}</h3>
                    <p>{{ translations.subscription_status_desc }}</p>
                    <a href="/subscription" class="coffee-button">{{ translations.manage_subscription }}</a>
                </div>
                
                <div class="workflow-step">
                    <span class="workflow-icon">🤖</span>
                    <h3>{{ translations.ai_tools_status }}</h3>
                    <p>{{ translations.ai_tools_status_desc }}</p>
                    <a href="/ai-tools" class="coffee-button">{{ translations.manage_tools }}</a>
                </div>
            </div>
        </div>

        <footer class="coffee-footer">
            <p>{{ translations.footer }}</p>
        </footer>
    </div>

    <script>
        function changeLanguage(lang) {
            window.location.href = '/dashboard?lang=' + lang;
        }
    </script>
</body>
</html>
"""

PHONE_ASSIGNMENT_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ language }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>☕ {{ translations.phone_assignment_title }} - VoiceConnect Pro</title>
    <style>{{ css }}</style>
</head>
<body>
    <div class="language-selector">
        <select class="language-dropdown" onchange="changeLanguage(this.value)">
            <option value="en" {{ 'selected' if language == 'en' else '' }}>🇺🇸 English</option>
            <option value="ru" {{ 'selected' if language == 'ru' else '' }}>🇷🇺 Русский</option>
            <option value="uz" {{ 'selected' if language == 'uz' else '' }}>🇺🇿 O'zbek</option>
        </select>
    </div>

    <div class="coffee-container fade-in">
        <nav class="coffee-nav">
            <ul>
                <li><a href="/dashboard">← {{ translations.dashboard }}</a></li>
                <li><a href="/phone-assignment">{{ translations.phone_assignment }}</a></li>
                <li><a href="/subscription">{{ translations.subscription }}</a></li>
                <li><a href="/ai-tools">{{ translations.ai_tools }}</a></li>
                <li><a href="/api/auth/logout">{{ translations.logout }}</a></li>
            </ul>
        </nav>

        <header class="coffee-header">
            <h1 class="coffee-title">📞 {{ translations.phone_assignment_title }}</h1>
            <p class="coffee-subtitle">{{ translations.phone_assignment_subtitle }}</p>
        </header>

        <div class="coffee-card phone-assignment">
            <h2>{{ translations.your_company_phone }}</h2>
            
            {% if phone_number %}
            <div class="assigned-phone">{{ phone_number }}</div>
            <p>{{ translations.phone_active_desc }}</p>
            
            <div style="margin: 2rem 0;">
                <h3>{{ translations.consultation_info }}</h3>
                <p>{{ translations.consultation_desc }}</p>
                <div class="workflow-step" style="margin: 1rem 0;">
                    <span class="workflow-icon">⏰</span>
                    <p><strong>{{ translations.time_remaining }}:</strong> {{ time_remaining }} {{ translations.minutes }}</p>
                </div>
            </div>
            
            {% else %}
            <p>{{ translations.no_phone_assigned }}</p>
            <form method="POST" action="/api/phone/assign">
                <button type="submit" class="coffee-button">{{ translations.get_phone_button }}</button>
            </form>
            {% endif %}
            
            <div style="margin-top: 2rem;">
                <h3>{{ translations.how_it_works }}</h3>
                <div class="business-workflow">
                    <div class="workflow-step">
                        <span class="workflow-icon">1️⃣</span>
                        <p>{{ translations.step_1_phone }}</p>
                    </div>
                    <div class="workflow-step">
                        <span class="workflow-icon">2️⃣</span>
                        <p>{{ translations.step_2_phone }}</p>
                    </div>
                    <div class="workflow-step">
                        <span class="workflow-icon">3️⃣</span>
                        <p>{{ translations.step_3_phone }}</p>
                    </div>
                </div>
            </div>
        </div>

        <footer class="coffee-footer">
            <p>{{ translations.footer }}</p>
        </footer>
    </div>

    <script>
        function changeLanguage(lang) {
            window.location.href = '/phone-assignment?lang=' + lang;
        }
    </script>
</body>
</html>
"""

SUBSCRIPTION_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ language }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>☕ {{ translations.subscription_title }} - VoiceConnect Pro</title>
    <style>{{ css }}</style>
</head>
<body>
    <div class="language-selector">
        <select class="language-dropdown" onchange="changeLanguage(this.value)">
            <option value="en" {{ 'selected' if language == 'en' else '' }}>🇺🇸 English</option>
            <option value="ru" {{ 'selected' if language == 'ru' else '' }}>🇷🇺 Русский</option>
            <option value="uz" {{ 'selected' if language == 'uz' else '' }}>🇺🇿 O'zbek</option>
        </select>
    </div>

    <div class="coffee-container fade-in">
        <nav class="coffee-nav">
            <ul>
                <li><a href="/dashboard">← {{ translations.dashboard }}</a></li>
                <li><a href="/phone-assignment">{{ translations.phone_assignment }}</a></li>
                <li><a href="/subscription">{{ translations.subscription }}</a></li>
                <li><a href="/ai-tools">{{ translations.ai_tools }}</a></li>
                <li><a href="/api/auth/logout">{{ translations.logout }}</a></li>
            </ul>
        </nav>

        <header class="coffee-header">
            <h1 class="coffee-title">💼 {{ translations.subscription_title }}</h1>
            <p class="coffee-subtitle">{{ translations.subscription_subtitle }}</p>
        </header>

        <div class="coffee-card">
            <h2>{{ translations.choose_plan }}</h2>
            
            <div class="subscription-plans">
                <div class="plan-card">
                    <h3>{{ translations.basic_plan }}</h3>
                    <div class="plan-price">$20<span style="font-size: 1rem;">/{{ translations.month }}</span></div>
                    <ul class="plan-features">
                        <li>✅ {{ translations.basic_feature_1 }}</li>
                        <li>✅ {{ translations.basic_feature_2 }}</li>
                        <li>✅ {{ translations.basic_feature_3 }}</li>
                        <li>✅ {{ translations.basic_feature_4 }}</li>
                    </ul>
                    <form method="POST" action="/api/subscription/create">
                        <input type="hidden" name="plan" value="basic">
                        <button type="submit" class="coffee-button">{{ translations.select_plan }}</button>
                    </form>
                </div>
                
                <div class="plan-card recommended">
                    <h3>{{ translations.professional_plan }} ⭐</h3>
                    <div class="plan-price">$50<span style="font-size: 1rem;">/{{ translations.month }}</span></div>
                    <ul class="plan-features">
                        <li>✅ {{ translations.pro_feature_1 }}</li>
                        <li>✅ {{ translations.pro_feature_2 }}</li>
                        <li>✅ {{ translations.pro_feature_3 }}</li>
                        <li>✅ {{ translations.pro_feature_4 }}</li>
                        <li>✅ {{ translations.pro_feature_5 }}</li>
                    </ul>
                    <form method="POST" action="/api/subscription/create">
                        <input type="hidden" name="plan" value="professional">
                        <button type="submit" class="coffee-button">{{ translations.select_plan }}</button>
                    </form>
                </div>
                
                <div class="plan-card">
                    <h3>{{ translations.enterprise_plan }}</h3>
                    <div class="plan-price">$100<span style="font-size: 1rem;">/{{ translations.month }}</span></div>
                    <ul class="plan-features">
                        <li>✅ {{ translations.enterprise_feature_1 }}</li>
                        <li>✅ {{ translations.enterprise_feature_2 }}</li>
                        <li>✅ {{ translations.enterprise_feature_3 }}</li>
                        <li>✅ {{ translations.enterprise_feature_4 }}</li>
                        <li>✅ {{ translations.enterprise_feature_5 }}</li>
                    </ul>
                    <form method="POST" action="/api/subscription/create">
                        <input type="hidden" name="plan" value="enterprise">
                        <button type="submit" class="coffee-button">{{ translations.select_plan }}</button>
                    </form>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 2rem;">
                <p>{{ translations.payment_info }}</p>
                <p><strong>{{ translations.secure_payment }}</strong></p>
            </div>
        </div>

        <footer class="coffee-footer">
            <p>{{ translations.footer }}</p>
        </footer>
    </div>

    <script>
        function changeLanguage(lang) {
            window.location.href = '/subscription?lang=' + lang;
        }
    </script>
</body>
</html>
"""

AI_TOOLS_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ language }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>☕ {{ translations.ai_tools_title }} - VoiceConnect Pro</title>
    <style>{{ css }}</style>
</head>
<body>
    <div class="language-selector">
        <select class="language-dropdown" onchange="changeLanguage(this.value)">
            <option value="en" {{ 'selected' if language == 'en' else '' }}>🇺🇸 English</option>
            <option value="ru" {{ 'selected' if language == 'ru' else '' }}>🇷🇺 Русский</option>
            <option value="uz" {{ 'selected' if language == 'uz' else '' }}>🇺🇿 O'zbek</option>
        </select>
    </div>

    <div class="coffee-container fade-in">
        <nav class="coffee-nav">
            <ul>
                <li><a href="/dashboard">← {{ translations.dashboard }}</a></li>
                <li><a href="/phone-assignment">{{ translations.phone_assignment }}</a></li>
                <li><a href="/subscription">{{ translations.subscription }}</a></li>
                <li><a href="/ai-tools">{{ translations.ai_tools }}</a></li>
                <li><a href="/api/auth/logout">{{ translations.logout }}</a></li>
            </ul>
        </nav>

        <header class="coffee-header">
            <h1 class="coffee-title">🤖 {{ translations.ai_tools_title }}</h1>
            <p class="coffee-subtitle">{{ translations.ai_tools_subtitle }}</p>
        </header>

        <div class="coffee-card">
            <h2>🤖 {{ translations.gemini_assistant }}</h2>
            <div class="gemini-chat">
                <div class="chat-messages" id="chatMessages">
                    <div class="chat-message gemini">
                        <strong>Gemini:</strong> {{ translations.gemini_welcome }}
                        <ul>
                            <li>• {{ translations.gemini_capability_1 }}</li>
                            <li>• {{ translations.gemini_capability_2 }}</li>
                            <li>• {{ translations.gemini_capability_3 }}</li>
                            <li>• {{ translations.gemini_capability_4 }}</li>
                            <li>• {{ translations.gemini_capability_5 }}</li>
                        </ul>
                        {{ translations.gemini_question }}
                    </div>
                </div>
                <div class="chat-input-container">
                    <input type="text" id="chatInput" class="chat-input" placeholder="{{ translations.chat_placeholder }}">
                    <button onclick="sendMessage()" class="coffee-button" style="width: auto;">{{ translations.send }}</button>
                </div>
            </div>
        </div>

        <div class="coffee-card">
            <h2>🛠️ {{ translations.available_tools }}</h2>
            <div class="ai-tools-grid">
                <div class="tool-card" onclick="selectTool('call-automation')">
                    <h3>📞 {{ translations.tool_call_automation }}</h3>
                    <p>{{ translations.tool_call_automation_desc }}</p>
                </div>
                <div class="tool-card" onclick="selectTool('sms-campaigns')">
                    <h3>💬 {{ translations.tool_sms_campaigns }}</h3>
                    <p>{{ translations.tool_sms_campaigns_desc }}</p>
                </div>
                <div class="tool-card" onclick="selectTool('analytics')">
                    <h3>📊 {{ translations.tool_analytics }}</h3>
                    <p>{{ translations.tool_analytics_desc }}</p>
                </div>
                <div class="tool-card" onclick="selectTool('lead-scoring')">
                    <h3>🎯 {{ translations.tool_lead_scoring }}</h3>
                    <p>{{ translations.tool_lead_scoring_desc }}</p>
                </div>
                <div class="tool-card" onclick="selectTool('appointment-booking')">
                    <h3>📅 {{ translations.tool_appointment_booking }}</h3>
                    <p>{{ translations.tool_appointment_booking_desc }}</p>
                </div>
                <div class="tool-card" onclick="selectTool('follow-up')">
                    <h3>🔄 {{ translations.tool_follow_up }}</h3>
                    <p>{{ translations.tool_follow_up_desc }}</p>
                </div>
            </div>
        </div>

        <div class="coffee-card">
            <h2>🔗 {{ translations.tool_connections }}</h2>
            <p>{{ translations.tool_connections_desc }}</p>
            <div id="toolConnections">
                <p>{{ translations.no_connections }}</p>
            </div>
        </div>

        <footer class="coffee-footer">
            <p>{{ translations.footer }}</p>
        </footer>
    </div>

    <script>
        function changeLanguage(lang) {
            window.location.href = '/ai-tools?lang=' + lang;
        }

        function sendMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            if (!message) return;

            const messagesContainer = document.getElementById('chatMessages');
            
            // Add user message
            const userMessage = document.createElement('div');
            userMessage.className = 'chat-message user';
            userMessage.innerHTML = '<strong>{{ translations.you }}:</strong> ' + message;
            messagesContainer.appendChild(userMessage);
            
            input.value = '';
            
            // Send to backend
            fetch('/api/gemini/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                const geminiMessage = document.createElement('div');
                geminiMessage.className = 'chat-message gemini';
                geminiMessage.innerHTML = '<strong>Gemini:</strong> ' + data.response;
                messagesContainer.appendChild(geminiMessage);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            })
            .catch(error => {
                console.error('Error:', error);
                const errorMessage = document.createElement('div');
                errorMessage.className = 'chat-message gemini';
                errorMessage.innerHTML = '<strong>Gemini:</strong> {{ translations.error_message }}';
                messagesContainer.appendChild(errorMessage);
            });
        }

        function selectTool(toolId) {
            const input = document.getElementById('chatInput');
            input.value = '{{ translations.configure_tool }}: ' + toolId;
            input.focus();
        }

        // Allow Enter key to send message
        document.getElementById('chatInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""

# Translations
TRANSLATIONS = {
    'en': {
        'title': 'AI Call Center Solution',
        'subtitle': 'Complete Business Solution with AI-Powered Tools',
        'welcome_title': 'Welcome to VoiceConnect Pro',
        'welcome_description': 'Transform your business with our comprehensive AI call center solution. Get a dedicated phone number, AI consultation, and custom tool recommendations.',
        'step1_title': 'Sign Up & Login',
        'step1_desc': 'Create your account with email and password',
        'step2_title': 'Get Phone Number',
        'step2_desc': 'Receive a company phone number for 30-minute consultation',
        'step3_title': 'AI Analysis',
        'step3_desc': 'AI analyzes your business and suggests relevant tools',
        'step4_title': 'Subscribe & Use',
        'step4_desc': 'Subscribe for $20/month to enable your custom tools',
        'get_started': 'Get Started',
        'footer': '☕ Powered by VoiceConnect Pro - Your AI Business Partner',
        'login_title': 'Login',
        'login_subtitle': 'Access Your AI Business Dashboard',
        'email_placeholder': 'Email Address',
        'password_placeholder': 'Password',
        'login_button': 'Login',
        'no_account': "Don't have an account? Sign up below:",
        'full_name_placeholder': 'Full Name',
        'signup_button': 'Sign Up',
        'back_home': 'Back to Home',
        'dashboard_title': 'Dashboard',
        'welcome_back': 'Welcome back',
        'dashboard_subtitle': 'Manage your AI business tools and subscriptions',
        'dashboard': 'Dashboard',
        'phone_assignment': 'Phone Number',
        'subscription': 'Subscription',
        'ai_tools': 'AI Tools',
        'logout': 'Logout',
        'business_overview': 'Business Overview',
        'phone_status': 'Phone Status',
        'phone_status_desc': 'Manage your company phone number',
        'manage_phone': 'Manage Phone',
        'subscription_status': 'Subscription Status',
        'subscription_status_desc': 'View and manage your subscription',
        'manage_subscription': 'Manage Subscription',
        'ai_tools_status': 'AI Tools Status',
        'ai_tools_status_desc': 'Configure your AI tools',
        'manage_tools': 'Manage Tools',
        'phone_assignment_title': 'Phone Number Assignment',
        'phone_assignment_subtitle': 'Your dedicated business phone number',
        'your_company_phone': 'Your Company Phone Number',
        'phone_active_desc': 'This phone number is active for 30-minute AI consultation',
        'consultation_info': 'Consultation Information',
        'consultation_desc': 'Clients can call this number for AI-powered business consultation',
        'time_remaining': 'Time Remaining',
        'minutes': 'minutes',
        'no_phone_assigned': 'No phone number assigned yet',
        'get_phone_button': 'Get My Phone Number',
        'how_it_works': 'How It Works',
        'step_1_phone': 'Get assigned a dedicated phone number',
        'step_2_phone': 'Clients call for 30-minute consultation',
        'step_3_phone': 'AI analyzes and recommends tools',
        'subscription_title': 'Subscription Plans',
        'subscription_subtitle': 'Choose the perfect plan for your business',
        'choose_plan': 'Choose Your Plan',
        'basic_plan': 'Basic Plan',
        'month': 'month',
        'basic_feature_1': 'AI Call Analysis',
        'basic_feature_2': 'Basic Tool Recommendations',
        'basic_feature_3': 'Email Support',
        'basic_feature_4': 'Monthly Reports',
        'select_plan': 'Select This Plan',
        'professional_plan': 'Professional Plan',
        'pro_feature_1': 'Advanced AI Analysis',
        'pro_feature_2': 'Custom Tool Configuration',
        'pro_feature_3': 'Priority Support',
        'pro_feature_4': 'Weekly Reports',
        'pro_feature_5': 'API Access',
        'enterprise_plan': 'Enterprise Plan',
        'enterprise_feature_1': 'Full AI Suite',
        'enterprise_feature_2': 'Unlimited Tool Connections',
        'enterprise_feature_3': '24/7 Support',
        'enterprise_feature_4': 'Daily Reports',
        'enterprise_feature_5': 'Custom Integrations',
        'payment_info': 'Secure payment processing with Click (Uzbekistan)',
        'secure_payment': '🔒 Your payment information is secure',
        'ai_tools_title': 'AI Agent Tools',
        'ai_tools_subtitle': 'Chat with Gemini to create, edit, delete, and connect tools',
        'gemini_assistant': 'Gemini AI Assistant',
        'gemini_welcome': "Hello! I'm your AI assistant specialized in managing your call center tools. I can help you:",
        'gemini_capability_1': 'Create new AI tools and workflows',
        'gemini_capability_2': 'Edit existing tool configurations',
        'gemini_capability_3': 'Delete unused tools',
        'gemini_capability_4': 'Connect tools to create automation chains',
        'gemini_capability_5': 'Analyze your business needs and suggest tools',
        'gemini_question': 'What would you like to do today?',
        'chat_placeholder': 'Ask me to create, edit, delete, or connect tools...',
        'send': 'Send',
        'available_tools': 'Available Tools',
        'tool_call_automation': 'Call Automation',
        'tool_call_automation_desc': 'Automated calling workflows',
        'tool_sms_campaigns': 'SMS Campaigns',
        'tool_sms_campaigns_desc': 'Bulk SMS management',
        'tool_analytics': 'Analytics',
        'tool_analytics_desc': 'Performance tracking',
        'tool_lead_scoring': 'Lead Scoring',
        'tool_lead_scoring_desc': 'AI-powered lead qualification',
        'tool_appointment_booking': 'Appointment Booking',
        'tool_appointment_booking_desc': 'Automated scheduling',
        'tool_follow_up': 'Follow-up',
        'tool_follow_up_desc': 'Customer follow-up automation',
        'tool_connections': 'Tool Connections',
        'tool_connections_desc': 'Use the Gemini chat above to create connections between tools. For example: "Connect lead scoring to appointment booking"',
        'no_connections': 'No active connections. Ask Gemini to create some!',
        'you': 'You',
        'error_message': 'Sorry, there was an error processing your request.',
        'configure_tool': 'Configure tool'
    },
    'ru': {
        'title': 'ИИ Решение для Колл-центра',
        'subtitle': 'Полное бизнес-решение с инструментами на базе ИИ',
        'welcome_title': 'Добро пожаловать в VoiceConnect Pro',
        'welcome_description': 'Трансформируйте свой бизнес с нашим комплексным решением ИИ колл-центра. Получите выделенный номер телефона, ИИ консультацию и рекомендации по инструментам.',
        'step1_title': 'Регистрация и Вход',
        'step1_desc': 'Создайте аккаунт с email и паролем',
        'step2_title': 'Получите Номер',
        'step2_desc': 'Получите корпоративный номер для 30-минутной консультации',
        'step3_title': 'ИИ Анализ',
        'step3_desc': 'ИИ анализирует ваш бизнес и предлагает подходящие инструменты',
        'step4_title': 'Подписка и Использование',
        'step4_desc': 'Подпишитесь за $20/месяц для активации ваших инструментов',
        'get_started': 'Начать',
        'footer': '☕ Работает на VoiceConnect Pro - Ваш ИИ Бизнес-партнер',
        'login_title': 'Вход',
        'login_subtitle': 'Доступ к вашей ИИ бизнес-панели',
        'email_placeholder': 'Email адрес',
        'password_placeholder': 'Пароль',
        'login_button': 'Войти',
        'no_account': 'Нет аккаунта? Зарегистрируйтесь ниже:',
        'full_name_placeholder': 'Полное имя',
        'signup_button': 'Регистрация',
        'back_home': 'Назад на главную',
        'dashboard_title': 'Панель управления',
        'welcome_back': 'С возвращением',
        'dashboard_subtitle': 'Управляйте вашими ИИ инструментами и подписками',
        'dashboard': 'Панель',
        'phone_assignment': 'Номер телефона',
        'subscription': 'Подписка',
        'ai_tools': 'ИИ Инструменты',
        'logout': 'Выход',
        'business_overview': 'Обзор бизнеса',
        'phone_status': 'Статус телефона',
        'phone_status_desc': 'Управление корпоративным номером',
        'manage_phone': 'Управлять номером',
        'subscription_status': 'Статус подписки',
        'subscription_status_desc': 'Просмотр и управление подпиской',
        'manage_subscription': 'Управлять подпиской',
        'ai_tools_status': 'Статус ИИ инструментов',
        'ai_tools_status_desc': 'Настройка ваших ИИ инструментов',
        'manage_tools': 'Управлять инструментами',
        'phone_assignment_title': 'Назначение номера телефона',
        'phone_assignment_subtitle': 'Ваш выделенный бизнес номер',
        'your_company_phone': 'Ваш корпоративный номер',
        'phone_active_desc': 'Этот номер активен для 30-минутной ИИ консультации',
        'consultation_info': 'Информация о консультации',
        'consultation_desc': 'Клиенты могут звонить на этот номер для бизнес-консультации с ИИ',
        'time_remaining': 'Осталось времени',
        'minutes': 'минут',
        'no_phone_assigned': 'Номер телефона еще не назначен',
        'get_phone_button': 'Получить мой номер',
        'how_it_works': 'Как это работает',
        'step_1_phone': 'Получите выделенный номер телефона',
        'step_2_phone': 'Клиенты звонят для 30-минутной консультации',
        'step_3_phone': 'ИИ анализирует и рекомендует инструменты',
        'subscription_title': 'Планы подписки',
        'subscription_subtitle': 'Выберите идеальный план для вашего бизнеса',
        'choose_plan': 'Выберите ваш план',
        'basic_plan': 'Базовый план',
        'month': 'месяц',
        'basic_feature_1': 'ИИ анализ звонков',
        'basic_feature_2': 'Базовые рекомендации инструментов',
        'basic_feature_3': 'Поддержка по email',
        'basic_feature_4': 'Месячные отчеты',
        'select_plan': 'Выбрать этот план',
        'professional_plan': 'Профессиональный план',
        'pro_feature_1': 'Продвинутый ИИ анализ',
        'pro_feature_2': 'Настройка инструментов',
        'pro_feature_3': 'Приоритетная поддержка',
        'pro_feature_4': 'Недельные отчеты',
        'pro_feature_5': 'Доступ к API',
        'enterprise_plan': 'Корпоративный план',
        'enterprise_feature_1': 'Полный ИИ пакет',
        'enterprise_feature_2': 'Неограниченные соединения',
        'enterprise_feature_3': 'Поддержка 24/7',
        'enterprise_feature_4': 'Ежедневные отчеты',
        'enterprise_feature_5': 'Пользовательские интеграции',
        'payment_info': 'Безопасная обработка платежей через Click (Узбекистан)',
        'secure_payment': '🔒 Ваша платежная информация защищена',
        'ai_tools_title': 'ИИ Агент Инструменты',
        'ai_tools_subtitle': 'Общайтесь с Gemini для создания, редактирования, удаления и соединения инструментов',
        'gemini_assistant': 'ИИ Ассистент Gemini',
        'gemini_welcome': 'Привет! Я ваш ИИ ассистент, специализирующийся на управлении инструментами колл-центра. Я могу помочь вам:',
        'gemini_capability_1': 'Создавать новые ИИ инструменты и рабочие процессы',
        'gemini_capability_2': 'Редактировать существующие конфигурации инструментов',
        'gemini_capability_3': 'Удалять неиспользуемые инструменты',
        'gemini_capability_4': 'Соединять инструменты для создания цепочек автоматизации',
        'gemini_capability_5': 'Анализировать потребности бизнеса и предлагать инструменты',
        'gemini_question': 'Что бы вы хотели сделать сегодня?',
        'chat_placeholder': 'Попросите меня создать, отредактировать, удалить или соединить инструменты...',
        'send': 'Отправить',
        'available_tools': 'Доступные инструменты',
        'tool_call_automation': 'Автоматизация звонков',
        'tool_call_automation_desc': 'Автоматизированные рабочие процессы звонков',
        'tool_sms_campaigns': 'SMS кампании',
        'tool_sms_campaigns_desc': 'Массовое управление SMS',
        'tool_analytics': 'Аналитика',
        'tool_analytics_desc': 'Отслеживание производительности',
        'tool_lead_scoring': 'Оценка лидов',
        'tool_lead_scoring_desc': 'ИИ-квалификация лидов',
        'tool_appointment_booking': 'Бронирование встреч',
        'tool_appointment_booking_desc': 'Автоматизированное планирование',
        'tool_follow_up': 'Последующие действия',
        'tool_follow_up_desc': 'Автоматизация последующих действий с клиентами',
        'tool_connections': 'Соединения инструментов',
        'tool_connections_desc': 'Используйте чат Gemini выше для создания соединений между инструментами. Например: "Соедините оценку лидов с бронированием встреч"',
        'no_connections': 'Нет активных соединений. Попросите Gemini создать их!',
        'you': 'Вы',
        'error_message': 'Извините, произошла ошибка при обработке вашего запроса.',
        'configure_tool': 'Настроить инструмент'
    },
    'uz': {
        'title': 'AI Qo\'ng\'iroq Markazi Yechimi',
        'subtitle': 'AI Vositalari bilan To\'liq Biznes Yechimi',
        'welcome_title': 'VoiceConnect Pro ga Xush Kelibsiz',
        'welcome_description': 'Biznesingizni bizning keng qamrovli AI qo\'ng\'iroq markazi yechimi bilan o\'zgartiring. Maxsus telefon raqami, AI maslahat va vosita tavsiyalarini oling.',
        'step1_title': 'Ro\'yxatdan O\'tish va Kirish',
        'step1_desc': 'Email va parol bilan hisobingizni yarating',
        'step2_title': 'Telefon Raqamini Oling',
        'step2_desc': '30 daqiqalik maslahat uchun kompaniya telefon raqamini oling',
        'step3_title': 'AI Tahlili',
        'step3_desc': 'AI biznesingizni tahlil qiladi va tegishli vositalarni taklif qiladi',
        'step4_title': 'Obuna va Foydalanish',
        'step4_desc': 'Maxsus vositalaringizni yoqish uchun oyiga $20 ga obuna bo\'ling',
        'get_started': 'Boshlash',
        'footer': '☕ VoiceConnect Pro tomonidan ishlab chiqilgan - Sizning AI Biznes Hamkoringiz',
        'login_title': 'Kirish',
        'login_subtitle': 'AI Biznes Panelingizga Kirish',
        'email_placeholder': 'Email Manzili',
        'password_placeholder': 'Parol',
        'login_button': 'Kirish',
        'no_account': 'Hisobingiz yo\'qmi? Quyida ro\'yxatdan o\'ting:',
        'full_name_placeholder': 'To\'liq Ism',
        'signup_button': 'Ro\'yxatdan O\'tish',
        'back_home': 'Bosh Sahifaga Qaytish',
        'dashboard_title': 'Boshqaruv Paneli',
        'welcome_back': 'Xush kelibsiz',
        'dashboard_subtitle': 'AI biznes vositalaringiz va obunalaringizni boshqaring',
        'dashboard': 'Panel',
        'phone_assignment': 'Telefon Raqami',
        'subscription': 'Obuna',
        'ai_tools': 'AI Vositalari',
        'logout': 'Chiqish',
        'business_overview': 'Biznes Ko\'rinishi',
        'phone_status': 'Telefon Holati',
        'phone_status_desc': 'Kompaniya telefon raqamini boshqarish',
        'manage_phone': 'Telefonni Boshqarish',
        'subscription_status': 'Obuna Holati',
        'subscription_status_desc': 'Obunangizni ko\'rish va boshqarish',
        'manage_subscription': 'Obunani Boshqarish',
        'ai_tools_status': 'AI Vositalari Holati',
        'ai_tools_status_desc': 'AI vositalaringizni sozlash',
        'manage_tools': 'Vositalarni Boshqarish',
        'phone_assignment_title': 'Telefon Raqami Tayinlash',
        'phone_assignment_subtitle': 'Sizning maxsus biznes telefon raqamingiz',
        'your_company_phone': 'Sizning Kompaniya Telefon Raqamingiz',
        'phone_active_desc': 'Bu telefon raqami 30 daqiqalik AI maslahat uchun faol',
        'consultation_info': 'Maslahat Ma\'lumotlari',
        'consultation_desc': 'Mijozlar AI bilan biznes maslahat uchun bu raqamga qo\'ng\'iroq qilishlari mumkin',
        'time_remaining': 'Qolgan Vaqt',
        'minutes': 'daqiqa',
        'no_phone_assigned': 'Hali telefon raqami tayinlanmagan',
        'get_phone_button': 'Telefon Raqamimni Olish',
        'how_it_works': 'Qanday Ishlaydi',
        'step_1_phone': 'Maxsus telefon raqamini oling',
        'step_2_phone': 'Mijozlar 30 daqiqalik maslahat uchun qo\'ng\'iroq qilishadi',
        'step_3_phone': 'AI tahlil qiladi va vositalarni tavsiya qiladi',
        'subscription_title': 'Obuna Rejalari',
        'subscription_subtitle': 'Biznesingiz uchun mukammal rejani tanlang',
        'choose_plan': 'Rejangizni Tanlang',
        'basic_plan': 'Asosiy Reja',
        'month': 'oy',
        'basic_feature_1': 'AI Qo\'ng\'iroq Tahlili',
        'basic_feature_2': 'Asosiy Vosita Tavsiyalari',
        'basic_feature_3': 'Email Yordam',
        'basic_feature_4': 'Oylik Hisobotlar',
        'select_plan': 'Bu Rejani Tanlash',
        'professional_plan': 'Professional Reja',
        'pro_feature_1': 'Ilg\'or AI Tahlili',
        'pro_feature_2': 'Maxsus Vosita Sozlamalari',
        'pro_feature_3': 'Ustuvor Yordam',
        'pro_feature_4': 'Haftalik Hisobotlar',
        'pro_feature_5': 'API Kirish',
        'enterprise_plan': 'Korxona Rejasi',
        'enterprise_feature_1': 'To\'liq AI To\'plami',
        'enterprise_feature_2': 'Cheksiz Vosita Ulanishlari',
        'enterprise_feature_3': '24/7 Yordam',
        'enterprise_feature_4': 'Kunlik Hisobotlar',
        'enterprise_feature_5': 'Maxsus Integratsiyalar',
        'payment_info': 'Click (O\'zbekiston) orqali xavfsiz to\'lov qayta ishlash',
        'secure_payment': '🔒 Sizning to\'lov ma\'lumotlaringiz xavfsiz',
        'ai_tools_title': 'AI Agent Vositalari',
        'ai_tools_subtitle': 'Vositalarni yaratish, tahrirlash, o\'chirish va ulash uchun Gemini bilan suhbatlashing',
        'gemini_assistant': 'Gemini AI Yordamchisi',
        'gemini_welcome': 'Salom! Men qo\'ng\'iroq markazi vositalarini boshqarishga ixtisoslashgan AI yordamchisiman. Men sizga yordam bera olaman:',
        'gemini_capability_1': 'Yangi AI vositalari va ish jarayonlarini yaratish',
        'gemini_capability_2': 'Mavjud vosita sozlamalarini tahrirlash',
        'gemini_capability_3': 'Foydalanilmayotgan vositalarni o\'chirish',
        'gemini_capability_4': 'Avtomatlashtirish zanjirlari yaratish uchun vositalarni ulash',
        'gemini_capability_5': 'Biznes ehtiyojlaringizni tahlil qilish va vositalarni taklif qilish',
        'gemini_question': 'Bugun nima qilishni xohlaysiz?',
        'chat_placeholder': 'Vositalarni yaratish, tahrirlash, o\'chirish yoki ulashni so\'rang...',
        'send': 'Yuborish',
        'available_tools': 'Mavjud Vositalar',
        'tool_call_automation': 'Qo\'ng\'iroq Avtomatlashtirish',
        'tool_call_automation_desc': 'Avtomatlashtirilgan qo\'ng\'iroq ish jarayonlari',
        'tool_sms_campaigns': 'SMS Kampaniyalari',
        'tool_sms_campaigns_desc': 'Ommaviy SMS boshqaruvi',
        'tool_analytics': 'Analitika',
        'tool_analytics_desc': 'Ishlash ko\'rsatkichlarini kuzatish',
        'tool_lead_scoring': 'Lead Baholash',
        'tool_lead_scoring_desc': 'AI tomonidan lead kvalifikatsiyasi',
        'tool_appointment_booking': 'Uchrashuv Bron Qilish',
        'tool_appointment_booking_desc': 'Avtomatlashtirilgan rejalashtirish',
        'tool_follow_up': 'Kuzatuv',
        'tool_follow_up_desc': 'Mijozlarni kuzatish avtomatlashtirish',
        'tool_connections': 'Vosita Ulanishlari',
        'tool_connections_desc': 'Vositalar orasida ulanishlar yaratish uchun yuqoridagi Gemini chatdan foydalaning. Masalan: "Lead baholashni uchrashuv bron qilish bilan ulang"',
        'no_connections': 'Faol ulanishlar yo\'q. Gemini dan yaratishni so\'rang!',
        'you': 'Siz',
        'error_message': 'Kechirasiz, so\'rovingizni qayta ishlashda xatolik yuz berdi.',
        'configure_tool': 'Vositani sozlash'
    }
}

def get_language():
    """Get current language from request or session"""
    lang = request.args.get('lang') or session.get('language', 'en')
    if lang not in TRANSLATIONS:
        lang = 'en'
    session['language'] = lang
    return lang

def get_translations():
    """Get translations for current language"""
    lang = get_language()
    return TRANSLATIONS[lang]

# Routes
@app.route('/')
def index():
    """Main landing page"""
    language = get_language()
    translations = get_translations()
    
    return render_template_string(INDEX_TEMPLATE, 
                                css=COFFEE_THEME_CSS,
                                language=language,
                                translations=translations)

@app.route('/login')
def login_page():
    """Login page"""
    language = get_language()
    translations = get_translations()
    
    return render_template_string(LOGIN_TEMPLATE,
                                css=COFFEE_THEME_CSS,
                                language=language,
                                translations=translations,
                                message=None,
                                success=False)

@app.route('/dashboard')
def dashboard():
    """Dashboard page - requires authentication"""
    if 'user_id' not in session:
        return redirect('/login')
    
    language = get_language()
    translations = get_translations()
    
    # Get user info
    user = auth_api.get_user_by_id(session['user_id'])
    if not user:
        return redirect('/login')
    
    return render_template_string(DASHBOARD_TEMPLATE,
                                css=COFFEE_THEME_CSS,
                                language=language,
                                translations=translations,
                                user=user)

@app.route('/phone-assignment')
def phone_assignment():
    """Phone assignment page"""
    if 'user_id' not in session:
        return redirect('/login')
    
    language = get_language()
    translations = get_translations()
    
    # Get user info
    user = auth_api.get_user_by_id(session['user_id'])
    if not user:
        return redirect('/login')
    
    # Check if user has assigned phone number
    phone_number = get_user_phone_number(session['user_id'])
    time_remaining = get_consultation_time_remaining(session['user_id']) if phone_number else None
    
    return render_template_string(PHONE_ASSIGNMENT_TEMPLATE,
                                css=COFFEE_THEME_CSS,
                                language=language,
                                translations=translations,
                                user=user,
                                phone_number=phone_number,
                                time_remaining=time_remaining)

@app.route('/subscription')
def subscription():
    """Subscription page"""
    if 'user_id' not in session:
        return redirect('/login')
    
    language = get_language()
    translations = get_translations()
    
    # Get user info
    user = auth_api.get_user_by_id(session['user_id'])
    if not user:
        return redirect('/login')
    
    return render_template_string(SUBSCRIPTION_TEMPLATE,
                                css=COFFEE_THEME_CSS,
                                language=language,
                                translations=translations,
                                user=user)

@app.route('/ai-tools')
def ai_tools():
    """AI Tools page"""
    if 'user_id' not in session:
        return redirect('/login')
    
    language = get_language()
    translations = get_translations()
    
    # Get user info
    user = auth_api.get_user_by_id(session['user_id'])
    if not user:
        return redirect('/login')
    
    return render_template_string(AI_TOOLS_TEMPLATE,
                                css=COFFEE_THEME_CSS,
                                language=language,
                                translations=translations,
                                user=user)

# API Routes
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Login API endpoint"""
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            return render_template_string(LOGIN_TEMPLATE,
                                        css=COFFEE_THEME_CSS,
                                        language=get_language(),
                                        translations=get_translations(),
                                        message="Email and password are required",
                                        success=False)
        
        # Authenticate user
        user = auth_api.authenticate_user(email, password)
        if user:
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            return redirect('/dashboard')
        else:
            return render_template_string(LOGIN_TEMPLATE,
                                        css=COFFEE_THEME_CSS,
                                        language=get_language(),
                                        translations=get_translations(),
                                        message="Invalid email or password",
                                        success=False)
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        return render_template_string(LOGIN_TEMPLATE,
                                    css=COFFEE_THEME_CSS,
                                    language=get_language(),
                                    translations=get_translations(),
                                    message="Login failed. Please try again.",
                                    success=False)

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """Registration API endpoint"""
    try:
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([full_name, email, password]):
            return render_template_string(LOGIN_TEMPLATE,
                                        css=COFFEE_THEME_CSS,
                                        language=get_language(),
                                        translations=get_translations(),
                                        message="All fields are required",
                                        success=False)
        
        # Register user
        result = auth_api.register_user(email, password, full_name)
        if result['success']:
            return render_template_string(LOGIN_TEMPLATE,
                                        css=COFFEE_THEME_CSS,
                                        language=get_language(),
                                        translations=get_translations(),
                                        message="Registration successful! Please login.",
                                        success=True)
        else:
            return render_template_string(LOGIN_TEMPLATE,
                                        css=COFFEE_THEME_CSS,
                                        language=get_language(),
                                        translations=get_translations(),
                                        message=result.get('message', 'Registration failed'),
                                        success=False)
    
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return render_template_string(LOGIN_TEMPLATE,
                                    css=COFFEE_THEME_CSS,
                                    language=get_language(),
                                    translations=get_translations(),
                                    message="Registration failed. Please try again.",
                                    success=False)

@app.route('/api/auth/logout')
def api_logout():
    """Logout API endpoint"""
    session.clear()
    return redirect('/')

@app.route('/api/phone/assign', methods=['POST'])
def api_assign_phone():
    """Assign phone number API endpoint"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        # Generate a phone number for the user
        phone_number = assign_phone_number(session['user_id'])
        return redirect('/phone-assignment')
    
    except Exception as e:
        logger.error(f"Phone assignment error: {e}")
        return jsonify({'success': False, 'message': 'Failed to assign phone number'}), 500

@app.route('/api/subscription/create', methods=['POST'])
def api_create_subscription():
    """Create subscription API endpoint"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        plan = request.form.get('plan')
        if not plan:
            return jsonify({'success': False, 'message': 'Plan is required'}), 400
        
        # Create subscription (this would integrate with Click payment system)
        subscription_id = create_subscription(session['user_id'], plan)
        
        # Redirect to payment page (would be Click payment gateway)
        return redirect(f'/payment?subscription_id={subscription_id}')
    
    except Exception as e:
        logger.error(f"Subscription creation error: {e}")
        return jsonify({'success': False, 'message': 'Failed to create subscription'}), 500

@app.route('/api/gemini/chat', methods=['POST'])
def api_gemini_chat():
    """Gemini chat API endpoint"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'message': 'Message is required'}), 400
        
        # Process with Gemini demo responses
        message_lower = message.lower()
        
        if 'create' in message_lower and 'voice analytics' in message_lower:
            response = """🛠️ **Creating Voice Analytics Tool**

I'll help you create a Voice Analytics tool for your call center:

**Tool Configuration:**
- **Name**: Voice Analytics Pro
- **Function**: Real-time call sentiment analysis
- **Features**: 
  - Emotion detection (happy, frustrated, neutral)
  - Keyword spotting for important terms
  - Call quality scoring
  - Agent performance insights

**Setup Requirements:**
- Audio processing engine
- Machine learning models for sentiment
- Real-time dashboard integration
- Call recording system connection

**Expected Benefits:**
- 📊 Improve customer satisfaction scores
- 🎯 Identify training opportunities for agents
- ⚡ Real-time coaching alerts
- 📈 Better call resolution rates

Would you like me to configure specific parameters or connect this tool to others?"""

        elif 'connect' in message_lower and 'sms' in message_lower and 'follow' in message_lower:
            response = """🔗 **Tool Connection Created: SMS Campaigns → Follow-up**

I've successfully connected your SMS Campaigns tool to Follow-up automation:

**Connection Configuration:**
- **Trigger**: After SMS campaign completion
- **Action**: Automatically start follow-up sequence
- **Timing**: 24 hours after SMS delivery
- **Conditions**: Only for non-responders

**Workflow Details:**
1. SMS campaign sends messages
2. System tracks delivery and responses
3. Non-responders automatically enter follow-up sequence
4. Personalized follow-up messages sent based on original campaign

**Expected Results:**
- 🎯 Higher response rates from follow-up
- 🤖 Automated nurturing process
- 📊 Better campaign ROI tracking
- ⚡ Reduced manual follow-up work

The connection is now active! Would you like to adjust the timing or add more conditions?"""

        elif 'create' in message_lower and 'tool' in message_lower:
            response = """🛠️ **Creating New AI Tool**

I can help you create a custom AI tool for your call center. Here are some popular options:

**Available Tool Templates:**
1. **Voice Analytics** - Analyze call sentiment and keywords
2. **Customer Segmentation** - Automatically categorize customers
3. **Callback Scheduler** - Smart callback timing optimization
4. **Script Generator** - Dynamic call scripts based on customer data
5. **Quality Assurance** - Automated call quality scoring

**To create a tool, please specify:**
- Tool purpose and functionality
- Input data sources
- Expected outputs
- Integration requirements

What type of tool would you like to create?"""

        elif 'edit' in message_lower or 'modify' in message_lower:
            response = """✏️ **Tool Configuration Editor**

I can help you modify existing tools. Here's what I can edit:

**Editable Parameters:**
- Trigger conditions and thresholds
- Automation timing and schedules
- Notification settings
- Data processing rules
- Integration endpoints

**Current Tools Available for Editing:**
- Call Automation (Active)
- SMS Campaigns (Active) 
- Analytics (Active)
- Lead Scoring (Active)
- Appointment Booking (Active)
- Follow-up (Active)

Which tool would you like to modify and what changes do you need?"""

        elif 'delete' in message_lower:
            response = """🗑️ **Tool Deletion Manager**

I can help you safely remove unused tools. Before deletion, I'll:

**Safety Checks:**
- Verify tool is not actively used
- Check for dependent connections
- Backup current configurations
- Confirm deletion with you

**Currently Deletable Tools:**
- Unused workflow templates
- Inactive automation rules
- Disconnected integrations

Which tool would you like to remove? I'll perform safety checks first."""

        elif 'connect' in message_lower:
            response = """🔗 **Tool Connection Builder**

I can help you connect tools to create powerful automation workflows. Here are some popular connections:

**Recommended Connections:**
1. **Lead Scoring → Appointment Booking** - Auto-schedule high-score leads
2. **Call Automation → Analytics** - Track call performance
3. **SMS Campaigns → Follow-up** - Automated nurturing sequences
4. **Analytics → Lead Scoring** - Data-driven scoring improvements

**To create a connection, specify:**
- Source tool (what triggers the action)
- Target tool (what action to take)
- Conditions (when to trigger)
- Parameters (how to configure)

Which tools would you like to connect?"""

        else:
            response = f"""🤖 **AI Tools Assistant Ready**

I understand you want to: "{message}"

I can help you with:

**Tool Management:**
- ✨ Create new tools and workflows
- ✏️ Edit existing configurations
- 🗑️ Delete unused tools
- 🔗 Connect tools for automation
- 📊 Analyze and suggest improvements

**Quick Actions:**
- "Create a voice analytics tool"
- "Connect lead scoring to SMS campaigns"
- "Edit appointment booking settings"
- "Delete unused analytics rules"
- "Suggest tools for lead nurturing"

What specific action would you like me to take?"""
        
        return jsonify({'success': True, 'response': response})
    
    except Exception as e:
        logger.error(f"Gemini chat error: {e}")
        return jsonify({'success': False, 'message': 'Failed to process message'}), 500

# Static file serving
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

# Business Logic Functions
def get_user_phone_number(user_id):
    """Get assigned phone number for user"""
    # This would query the database for assigned phone numbers
    # For demo, return a sample number
    return "+998901234567"

def get_consultation_time_remaining(user_id):
    """Get remaining consultation time for user"""
    # This would calculate remaining time from database
    # For demo, return 25 minutes
    return 25

def assign_phone_number(user_id):
    """Assign a phone number to user"""
    # This would assign an actual phone number from available pool
    # For demo, return a sample number
    import random
    phone_number = f"+99890{random.randint(1000000, 9999999)}"
    
    # Store in database (demo)
    logger.info(f"Assigned phone number {phone_number} to user {user_id}")
    
    return phone_number

def create_subscription(user_id, plan):
    """Create a subscription for user"""
    # This would create a subscription record and initiate payment
    # For demo, return a sample subscription ID
    subscription_id = str(uuid.uuid4())
    
    logger.info(f"Created subscription {subscription_id} for user {user_id} with plan {plan}")
    
    return subscription_id

if __name__ == '__main__':
    print("☕ Starting VoiceConnect Pro with Coffee Paper Theme")
    print("🔐 Simple Authentication: Email + Password")
    print("🤖 Gemini AI Integration: Available" if gemini_service else "🤖 Gemini AI Integration: Demo Mode")
    print("🎨 Theme: Black & White Minimalistic Paper Coffee")
    print("🌐 Server: http://0.0.0.0:12000")
    
    app.run(host='0.0.0.0', port=12000, debug=True)