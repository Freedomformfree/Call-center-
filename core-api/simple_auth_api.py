"""
Simple Authentication API - Email and Password Only
No SMS verification required
"""

from flask import Flask, request, jsonify, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import logging
from datetime import datetime
import secrets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAuthAPI:
    def __init__(self, app=None, db_path="ai_call_center.db"):
        self.app = app
        self.db_path = db_path
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the Flask app with authentication routes"""
        app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
        
        # Initialize database
        self.init_database()
        
        # Register routes
        app.add_url_rule('/login', 'login_page', self.login_page, methods=['GET'])
        app.add_url_rule('/api/auth/login', 'api_login', self.api_login, methods=['POST'])
        app.add_url_rule('/api/auth/register', 'api_register', self.api_register, methods=['POST'])
        app.add_url_rule('/api/auth/logout', 'api_logout', self.api_logout, methods=['POST'])
        app.add_url_rule('/api/auth/check', 'api_check_auth', self.api_check_auth, methods=['GET'])
        app.add_url_rule('/dashboard', 'dashboard', self.dashboard, methods=['GET'])
    
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
            
            # Create sessions table for better session management
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_token TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def login_page(self):
        """Serve the login page"""
        try:
            with open('static/simple-login.html', 'r') as f:
                return f.read()
        except FileNotFoundError:
            return '''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>☕ Login - VoiceConnect Pro</title>
                <style>
                    body { font-family: Georgia, serif; background: #fefefe; color: #1a1a1a; margin: 0; padding: 20px; }
                    .container { max-width: 400px; margin: 50px auto; padding: 40px; border: 1px solid #e0e0e0; background: white; }
                    h1 { text-align: center; margin-bottom: 30px; }
                    input { width: 100%; padding: 12px; margin: 10px 0; border: 2px solid #e0e0e0; font-size: 16px; }
                    button { width: 100%; padding: 12px; background: #1a1a1a; color: white; border: none; font-size: 16px; cursor: pointer; }
                    button:hover { background: #2d2d2d; }
                    .form-group { margin-bottom: 20px; }
                    .text-center { text-align: center; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>☕ Welcome Back</h1>
                    <form id="loginForm">
                        <div class="form-group">
                            <input type="email" id="email" placeholder="Email Address" required>
                        </div>
                        <div class="form-group">
                            <input type="password" id="password" placeholder="Password" required>
                        </div>
                        <button type="submit">Sign In</button>
                    </form>
                    <div class="text-center">
                        <p>Don't have an account? <a href="#" onclick="showSignup()">Sign up here</a></p>
                    </div>
                </div>
                
                <script>
                    document.getElementById('loginForm').addEventListener('submit', async (e) => {
                        e.preventDefault();
                        const email = document.getElementById('email').value;
                        const password = document.getElementById('password').value;
                        
                        try {
                            const response = await fetch('/api/auth/login', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ email, password })
                            });
                            
                            const result = await response.json();
                            if (result.success) {
                                window.location.href = '/dashboard';
                            } else {
                                alert(result.message || 'Login failed');
                            }
                        } catch (error) {
                            alert('Network error. Please try again.');
                        }
                    });
                    
                    function showSignup() {
                        alert('Signup functionality available in the full application');
                    }
                </script>
            </body>
            </html>
            '''
    
    def api_login(self):
        """Handle login API request"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'No data provided'
                }), 400
            
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            
            if not email or not password:
                return jsonify({
                    'success': False,
                    'message': 'Email and password are required'
                }), 400
            
            # Check user credentials
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, full_name, email, password_hash, is_active 
                FROM users 
                WHERE email = ? AND is_active = 1
            ''', (email,))
            
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'Invalid email or password'
                }), 401
            
            user_id, full_name, user_email, password_hash, is_active = user
            
            # Verify password
            if not check_password_hash(password_hash, password):
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'Invalid email or password'
                }), 401
            
            # Update last login
            cursor.execute('''
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            # Set session
            session['user_id'] = user_id
            session['user_email'] = user_email
            session['user_name'] = full_name
            session['logged_in'] = True
            
            logger.info(f"User {email} logged in successfully")
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user_id,
                    'name': full_name,
                    'email': user_email
                }
            })
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({
                'success': False,
                'message': 'Internal server error'
            }), 500
    
    def api_register(self):
        """Handle registration API request"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'No data provided'
                }), 400
            
            full_name = data.get('full_name', '').strip()
            email = data.get('email', '').strip().lower()
            company = data.get('company', '').strip()
            phone = data.get('phone', '').strip()
            password = data.get('password', '')
            
            # Validation
            if not all([full_name, email, password]):
                return jsonify({
                    'success': False,
                    'message': 'Full name, email, and password are required'
                }), 400
            
            if len(password) < 6:
                return jsonify({
                    'success': False,
                    'message': 'Password must be at least 6 characters long'
                }), 400
            
            # Check if user already exists
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'Email already registered'
                }), 409
            
            # Create new user
            password_hash = generate_password_hash(password)
            
            cursor.execute('''
                INSERT INTO users (full_name, email, company, phone, password_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', (full_name, email, company, phone, password_hash))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"New user registered: {email}")
            
            return jsonify({
                'success': True,
                'message': 'Account created successfully',
                'user': {
                    'id': user_id,
                    'name': full_name,
                    'email': email
                }
            })
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return jsonify({
                'success': False,
                'message': 'Internal server error'
            }), 500
    
    def api_logout(self):
        """Handle logout API request"""
        try:
            session.clear()
            return jsonify({
                'success': True,
                'message': 'Logged out successfully'
            })
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return jsonify({
                'success': False,
                'message': 'Logout failed'
            }), 500
    
    def api_check_auth(self):
        """Check if user is authenticated"""
        try:
            if session.get('logged_in') and session.get('user_id'):
                return jsonify({
                    'success': True,
                    'authenticated': True,
                    'user': {
                        'id': session.get('user_id'),
                        'name': session.get('user_name'),
                        'email': session.get('user_email')
                    }
                })
            else:
                return jsonify({
                    'success': True,
                    'authenticated': False
                })
        except Exception as e:
            logger.error(f"Auth check error: {e}")
            return jsonify({
                'success': False,
                'message': 'Auth check failed'
            }), 500
    
    def dashboard(self):
        """Serve the dashboard page (requires authentication)"""
        if not session.get('logged_in'):
            return '''
            <script>
                alert('Please log in to access the dashboard');
                window.location.href = '/login';
            </script>
            '''
        
        user_name = session.get('user_name', 'User')
        user_email = session.get('user_email', '')
        
        return f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>☕ Dashboard - VoiceConnect Pro</title>
            <link rel="stylesheet" href="/static/coffee-paper-theme.css">
        </head>
        <body>
            <div class="paper-container">
                <header class="coffee-header">
                    <h1 class="coffee-title">Dashboard</h1>
                    <p class="coffee-subtitle">Welcome back, {user_name}!</p>
                </header>
                
                <section class="coffee-m-8">
                    <div class="coffee-card">
                        <h3>Account Information</h3>
                        <p class="coffee-font-mono">Email: {user_email}</p>
                        <p class="coffee-font-mono">Name: {user_name}</p>
                    </div>
                    
                    <div class="coffee-card coffee-m-6">
                        <h3>Quick Actions</h3>
                        <div class="coffee-grid coffee-grid-2">
                            <a href="/ai-tools" class="coffee-btn">
                                <span>🤖 AI Tools</span>
                            </a>
                            <a href="/analytics" class="coffee-btn">
                                <span>📊 Analytics</span>
                            </a>
                            <a href="/campaigns" class="coffee-btn">
                                <span>📞 Campaigns</span>
                            </a>
                            <a href="/settings" class="coffee-btn">
                                <span>⚙️ Settings</span>
                            </a>
                        </div>
                    </div>
                    
                    <div class="coffee-text-center coffee-m-6">
                        <button onclick="logout()" class="coffee-btn">
                            <span>🚪 Logout</span>
                        </button>
                    </div>
                </section>
            </div>
            
            <script>
                async function logout() {{
                    try {{
                        const response = await fetch('/api/auth/logout', {{
                            method: 'POST'
                        }});
                        
                        if (response.ok) {{
                            window.location.href = '/login';
                        }}
                    }} catch (error) {{
                        console.error('Logout error:', error);
                        alert('Logout failed');
                    }}
                }}
            </script>
        </body>
        </html>
        '''

def create_simple_auth_app():
    """Create a Flask app with simple authentication"""
    app = Flask(__name__)
    auth = SimpleAuthAPI(app)
    
    @app.route('/')
    def home():
        try:
            with open('static/index.html', 'r') as f:
                return f.read()
        except FileNotFoundError:
            return '<h1>Welcome to VoiceConnect Pro</h1><p><a href="/login">Login</a></p>'
    
    return app

if __name__ == '__main__':
    app = create_simple_auth_app()
    app.run(host='0.0.0.0', port=12000, debug=True)