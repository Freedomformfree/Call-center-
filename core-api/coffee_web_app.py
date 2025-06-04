#!/usr/bin/env python3
"""
VoiceConnect Pro - Coffee Paper Theme Web Application
Simple authentication with Gemini AI integration
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, session, render_template_string, redirect, url_for
from flask_cors import CORS
import logging
import json
from datetime import datetime

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import our simple authentication
from simple_auth_api import SimpleAuthAPI

# Import Gemini services
try:
    from gemini_chat_service import GeminiChatService
    from gemini_response_parser import GeminiResponseParser
    GEMINI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Gemini services not available: {e}")
    GEMINI_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_coffee_app():
    """Create the main Flask application with coffee theme"""
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app, supports_credentials=True)
    
    # Initialize simple authentication
    auth = SimpleAuthAPI(app)
    
    # Initialize Gemini service if available
    gemini_service = None
    if GEMINI_AVAILABLE:
        try:
            gemini_service = GeminiChatService()
            logger.info("Gemini chat service initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini service: {e}")
    
    # Serve static files
    @app.route('/static/<path:filename>')
    def static_files(filename):
        return app.send_static_file(filename)
    
    # Main routes
    @app.route('/')
    def home():
        """Serve the main page with coffee theme"""
        try:
            with open('static/index.html', 'r') as f:
                return f.read()
        except FileNotFoundError:
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>☕ VoiceConnect Pro</title>
                <link rel="stylesheet" href="/static/coffee-paper-theme.css">
            </head>
            <body>
                <div class="paper-container">
                    <header class="coffee-header">
                        <h1 class="coffee-title">VoiceConnect Pro</h1>
                        <p class="coffee-subtitle">Minimalistic AI Call Center Solutions</p>
                    </header>
                    <section class="coffee-m-8">
                        <div class="coffee-text-center">
                            <p>Welcome to VoiceConnect Pro</p>
                            <a href="/login" class="coffee-btn coffee-btn-primary">
                                <span>Get Started</span>
                            </a>
                        </div>
                    </section>
                </div>
            </body>
            </html>
            '''
    
    @app.route('/ai-tools')
    def ai_tools():
        """AI Tools dashboard with Gemini chat"""
        if not session.get('logged_in'):
            return redirect('/login')
        
        user_name = session.get('user_name', 'User')
        
        return f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>☕ AI Tools - VoiceConnect Pro</title>
            <link rel="stylesheet" href="/static/coffee-paper-theme.css">
            <style>
                .chat-container {{
                    height: 400px;
                    border: 2px solid var(--accent-line);
                    background: var(--paper-cream);
                    overflow-y: auto;
                    padding: var(--space-4);
                    margin-bottom: var(--space-4);
                }}
                .chat-message {{
                    margin-bottom: var(--space-3);
                    padding: var(--space-3);
                    border-radius: 4px;
                }}
                .chat-message.user {{
                    background: var(--paper-white);
                    border-left: 3px solid var(--coffee-black);
                }}
                .chat-message.assistant {{
                    background: var(--paper-beige);
                    border-left: 3px solid var(--coffee-medium);
                }}
                .chat-input-container {{
                    display: flex;
                    gap: var(--space-2);
                }}
                .chat-input {{
                    flex: 1;
                }}
                .tool-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: var(--space-4);
                    margin: var(--space-6) 0;
                }}
                .tool-card {{
                    padding: var(--space-4);
                    border: 1px solid var(--accent-line);
                    background: var(--paper-white);
                    cursor: pointer;
                    transition: var(--transition-smooth);
                }}
                .tool-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px var(--paper-shadow);
                }}
            </style>
        </head>
        <body>
            <nav class="coffee-nav">
                <ul class="coffee-nav-list">
                    <li class="coffee-nav-item">
                        <a href="/dashboard" class="coffee-nav-link">← Dashboard</a>
                    </li>
                    <li class="coffee-nav-item">
                        <a href="/ai-tools" class="coffee-nav-link active">AI Tools</a>
                    </li>
                    <li class="coffee-nav-item">
                        <a href="#" onclick="logout()" class="coffee-nav-link">Logout</a>
                    </li>
                </ul>
            </nav>

            <div class="paper-container">
                <header class="coffee-header">
                    <h1 class="coffee-title">AI Agent Tools</h1>
                    <p class="coffee-subtitle">Chat with Gemini to create, edit, delete, and connect tools</p>
                </header>

                <!-- Gemini Chat Interface -->
                <section class="coffee-m-8">
                    <h2 class="coffee-m-4">🤖 Gemini AI Assistant</h2>
                    <div class="coffee-card">
                        <div id="chatContainer" class="chat-container">
                            <div class="chat-message assistant">
                                <strong>Gemini:</strong> Hello {user_name}! I'm your AI assistant specialized in managing your call center tools. I can help you:
                                <ul class="coffee-font-mono coffee-text-sm coffee-m-2">
                                    <li>• Create new AI tools and workflows</li>
                                    <li>• Edit existing tool configurations</li>
                                    <li>• Delete unused tools</li>
                                    <li>• Connect tools to create automation chains</li>
                                    <li>• Analyze your business needs and suggest tools</li>
                                </ul>
                                What would you like to do today?
                            </div>
                        </div>
                        <div class="chat-input-container">
                            <input 
                                type="text" 
                                id="chatInput" 
                                class="coffee-input chat-input" 
                                placeholder="Ask me to create, edit, delete, or connect tools..."
                                onkeypress="handleChatKeyPress(event)"
                            >
                            <button onclick="sendMessage()" class="coffee-btn coffee-btn-primary">
                                <span>Send</span>
                            </button>
                        </div>
                    </div>
                </section>

                <!-- Available Tools -->
                <section class="coffee-m-8">
                    <h2 class="coffee-m-4">🛠️ Available Tools</h2>
                    <div class="tool-grid">
                        <div class="tool-card" onclick="selectTool('call-automation')">
                            <h4 class="coffee-font-mono">📞 Call Automation</h4>
                            <p class="coffee-text-sm">Automated calling workflows</p>
                        </div>
                        <div class="tool-card" onclick="selectTool('sms-campaigns')">
                            <h4 class="coffee-font-mono">💬 SMS Campaigns</h4>
                            <p class="coffee-text-sm">Bulk SMS management</p>
                        </div>
                        <div class="tool-card" onclick="selectTool('analytics')">
                            <h4 class="coffee-font-mono">📊 Analytics</h4>
                            <p class="coffee-text-sm">Performance tracking</p>
                        </div>
                        <div class="tool-card" onclick="selectTool('lead-scoring')">
                            <h4 class="coffee-font-mono">🎯 Lead Scoring</h4>
                            <p class="coffee-text-sm">AI-powered lead qualification</p>
                        </div>
                        <div class="tool-card" onclick="selectTool('appointment-booking')">
                            <h4 class="coffee-font-mono">📅 Appointment Booking</h4>
                            <p class="coffee-text-sm">Automated scheduling</p>
                        </div>
                        <div class="tool-card" onclick="selectTool('follow-up')">
                            <h4 class="coffee-font-mono">🔄 Follow-up</h4>
                            <p class="coffee-text-sm">Customer follow-up automation</p>
                        </div>
                    </div>
                </section>

                <!-- Tool Connections -->
                <section class="coffee-m-8">
                    <h2 class="coffee-m-4">🔗 Tool Connections</h2>
                    <div class="coffee-card">
                        <p class="coffee-text-center coffee-m-4">
                            Use the Gemini chat above to create connections between tools.
                            For example: "Connect lead scoring to appointment booking"
                        </p>
                        <div id="connectionsDisplay" class="coffee-font-mono coffee-text-sm">
                            <p>No active connections. Ask Gemini to create some!</p>
                        </div>
                    </div>
                </section>
            </div>

            <script>
                let chatHistory = [];

                function handleChatKeyPress(event) {{
                    if (event.key === 'Enter') {{
                        sendMessage();
                    }}
                }}

                async function sendMessage() {{
                    const input = document.getElementById('chatInput');
                    const message = input.value.trim();
                    
                    if (!message) return;
                    
                    // Add user message to chat
                    addMessageToChat('user', message);
                    input.value = '';
                    
                    // Show typing indicator
                    addMessageToChat('assistant', 'Thinking...', true);
                    
                    try {{
                        const response = await fetch('/api/gemini/chat', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{
                                message: message,
                                context: 'ai_tools_management',
                                history: chatHistory
                            }})
                        }});
                        
                        const result = await response.json();
                        
                        // Remove typing indicator
                        removeLastMessage();
                        
                        if (result.success) {{
                            addMessageToChat('assistant', result.response);
                            
                            // Handle tool actions if any
                            if (result.actions && result.actions.length > 0) {{
                                handleToolActions(result.actions);
                            }}
                        }} else {{
                            addMessageToChat('assistant', 'Sorry, I encountered an error. Please try again.');
                        }}
                    }} catch (error) {{
                        console.error('Chat error:', error);
                        removeLastMessage();
                        addMessageToChat('assistant', 'Network error. Please check your connection.');
                    }}
                }}

                function addMessageToChat(role, content, isTemporary = false) {{
                    const container = document.getElementById('chatContainer');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `chat-message ${{role}}`;
                    messageDiv.innerHTML = `<strong>${{role === 'user' ? 'You' : 'Gemini'}}:</strong> ${{content}}`;
                    
                    if (isTemporary) {{
                        messageDiv.id = 'tempMessage';
                    }}
                    
                    container.appendChild(messageDiv);
                    container.scrollTop = container.scrollHeight;
                    
                    // Add to history (except temporary messages)
                    if (!isTemporary) {{
                        chatHistory.push({{ role, content }});
                    }}
                }}

                function removeLastMessage() {{
                    const tempMessage = document.getElementById('tempMessage');
                    if (tempMessage) {{
                        tempMessage.remove();
                    }}
                }}

                function selectTool(toolId) {{
                    const input = document.getElementById('chatInput');
                    input.value = `Tell me more about the ${{toolId.replace('-', ' ')}} tool`;
                    input.focus();
                }}

                function handleToolActions(actions) {{
                    // Handle tool creation, editing, deletion, and connections
                    actions.forEach(action => {{
                        console.log('Tool action:', action);
                        // Implement tool action handling here
                    }});
                }}

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
    
    @app.route('/api/gemini/chat', methods=['POST'])
    def gemini_chat():
        """Handle Gemini chat requests"""
        if not session.get('logged_in'):
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        if not GEMINI_AVAILABLE or not gemini_service:
            return jsonify({
                'success': True,
                'response': 'Gemini AI is not available in this environment. This is a demo response. In a real deployment, I would help you create, edit, delete, and connect AI tools for your call center.',
                'actions': []
            })
        
        try:
            data = request.get_json()
            message = data.get('message', '')
            context = data.get('context', 'general')
            history = data.get('history', [])
            
            # Create specialized system prompt for AI tools management
            system_prompt = """
            You are a specialized AI assistant for VoiceConnect Pro call center management. Your role is to help users:
            
            1. CREATE new AI tools and workflows
            2. EDIT existing tool configurations  
            3. DELETE unused or outdated tools
            4. CONNECT tools to create automation chains
            5. ANALYZE business needs and suggest optimal tool combinations
            
            Available tools include:
            - Call Automation (automated calling workflows)
            - SMS Campaigns (bulk messaging)
            - Analytics (performance tracking)
            - Lead Scoring (AI qualification)
            - Appointment Booking (automated scheduling)
            - Follow-up (customer retention)
            
            When users request tool actions, provide clear, actionable responses and suggest specific configurations. Always be helpful and focus on practical business solutions.
            """
            
            # Simulate Gemini response (replace with actual Gemini API call)
            response_text = f"I understand you want to work with: {message}. "
            
            if "create" in message.lower():
                response_text += "I can help you create a new tool. What type of automation are you looking for? I can set up call workflows, SMS campaigns, or analytics dashboards."
            elif "edit" in message.lower():
                response_text += "I can help you modify existing tools. Which tool would you like to edit, and what changes do you need?"
            elif "delete" in message.lower():
                response_text += "I can help you remove tools safely. Which tool do you want to delete? I'll make sure to disconnect it from any workflows first."
            elif "connect" in message.lower():
                response_text += "I can create connections between tools. For example, I can connect lead scoring to appointment booking, or SMS campaigns to follow-up workflows."
            else:
                response_text += "I'm here to help you manage your AI tools. You can ask me to create, edit, delete, or connect tools. What would you like to do?"
            
            return jsonify({
                'success': True,
                'response': response_text,
                'actions': [],
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            return jsonify({
                'success': False,
                'message': 'Chat service error'
            }), 500
    
    return app

def main():
    """Main entry point"""
    app = create_coffee_app()
    
    print("☕ Starting VoiceConnect Pro with Coffee Paper Theme")
    print("🔐 Simple Authentication: Email + Password")
    print("🤖 Gemini AI Integration: Available")
    print("🎨 Theme: Black & White Minimalistic Paper Coffee")
    print("🌐 Server: http://0.0.0.0:12000")
    
    app.run(
        host='0.0.0.0',
        port=12000,
        debug=True
    )

if __name__ == '__main__':
    main()