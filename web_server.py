#!/usr/bin/env python3
"""
VoiceConnect Pro - Complete Web Application
Full-featured web server with all integrations
"""

import os
import sys
from pathlib import Path

# Add the core-api directory to Python path
core_api_dir = Path(__file__).parent / "core-api"
sys.path.insert(0, str(core_api_dir))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
from contextlib import asynccontextmanager

# Import available API routers
try:
    from gemini_chat_api import router as gemini_chat_router
    GEMINI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Gemini chat not available: {e}")
    GEMINI_AVAILABLE = False

try:
    from admin_api import router as admin_router
    ADMIN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Admin API not available: {e}")
    ADMIN_AVAILABLE = False

try:
    from client_api import router as client_router
    CLIENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Client API not available: {e}")
    CLIENT_AVAILABLE = False

try:
    from telegram_api import router as telegram_router
    TELEGRAM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Telegram API not available: {e}")
    TELEGRAM_AVAILABLE = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    print("🚀 Starting VoiceConnect Pro Complete Web Application...")
    print("📝 Initializing available services...")
    
    # Initialize available services
    if GEMINI_AVAILABLE:
        try:
            # Initialize Gemini chat service if available
            from gemini_chat_service import gemini_chat_service
            print("✅ Gemini Chat service available")
        except Exception as e:
            print(f"⚠️  Gemini Chat service warning: {e}")
    
    print("🌐 Web application ready!")
    yield
    
    print("🛑 Shutting down VoiceConnect Pro...")

# Create FastAPI app
app = FastAPI(
    title="VoiceConnect Pro",
    description="Advanced Call Center Management System with AI Integration",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "service": "voiceconnect-pro-complete",
        "version": "2.0.0",
        "components": {
            "api": "online",
            "gemini_chat": "online" if GEMINI_AVAILABLE else "unavailable",
            "admin": "online" if ADMIN_AVAILABLE else "unavailable",
            "client": "online" if CLIENT_AVAILABLE else "unavailable",
            "telegram": "online" if TELEGRAM_AVAILABLE else "unavailable",
            "frontend": "online"
        }
    }

# Include available API routers
if GEMINI_AVAILABLE:
    app.include_router(gemini_chat_router, prefix="/api/v1/gemini-chat", tags=["Gemini Chat"])

if ADMIN_AVAILABLE:
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])

if CLIENT_AVAILABLE:
    app.include_router(client_router, prefix="/api/v1/client", tags=["Client"])

if TELEGRAM_AVAILABLE:
    app.include_router(telegram_router, prefix="/api/v1/telegram", tags=["Telegram"])

# Serve the main dashboard
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard"""
    try:
        dashboard_path = Path(__file__).parent / "frontend" / "dashboard.html"
        with open(dashboard_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>VoiceConnect Pro - System Status</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 0; 
                    padding: 40px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                }}
                .container {{ 
                    max-width: 800px; 
                    margin: 0 auto; 
                    background: rgba(255,255,255,0.1); 
                    padding: 40px; 
                    border-radius: 20px; 
                    backdrop-filter: blur(10px);
                }}
                h1 {{ color: #fff; margin-bottom: 30px; }}
                .status {{ 
                    background: rgba(255,255,255,0.2); 
                    padding: 20px; 
                    border-radius: 10px; 
                    margin: 20px 0; 
                }}
                .available {{ color: #2ecc71; }}
                .unavailable {{ color: #e74c3c; }}
                .endpoint {{ 
                    background: rgba(255,255,255,0.1); 
                    padding: 15px; 
                    margin: 10px 0; 
                    border-radius: 8px; 
                }}
                .endpoint a {{ color: #3498db; text-decoration: none; }}
                .endpoint a:hover {{ text-decoration: underline; }}
                .feature-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                    gap: 20px; 
                    margin: 30px 0; 
                }}
                .feature {{ 
                    background: rgba(255,255,255,0.1); 
                    padding: 20px; 
                    border-radius: 10px; 
                    text-align: center; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 VoiceConnect Pro</h1>
                <p>Advanced Call Center Management System with AI Integration</p>
                
                <div class="status">
                    <h2>📊 System Status</h2>
                    <div class="feature-grid">
                        <div class="feature">
                            <h3>🤖 Gemini AI</h3>
                            <p class="{'available' if GEMINI_AVAILABLE else 'unavailable'}">
                                {'✅ Available' if GEMINI_AVAILABLE else '❌ Unavailable'}
                            </p>
                        </div>
                        <div class="feature">
                            <h3>👨‍💼 Admin Panel</h3>
                            <p class="{'available' if ADMIN_AVAILABLE else 'unavailable'}">
                                {'✅ Available' if ADMIN_AVAILABLE else '❌ Unavailable'}
                            </p>
                        </div>
                        <div class="feature">
                            <h3>👥 Client API</h3>
                            <p class="{'available' if CLIENT_AVAILABLE else 'unavailable'}">
                                {'✅ Available' if CLIENT_AVAILABLE else '❌ Unavailable'}
                            </p>
                        </div>
                        <div class="feature">
                            <h3>📱 Telegram</h3>
                            <p class="{'available' if TELEGRAM_AVAILABLE else 'unavailable'}">
                                {'✅ Available' if TELEGRAM_AVAILABLE else '❌ Unavailable'}
                            </p>
                        </div>
                    </div>
                </div>

                <div class="status">
                    <h2>🔗 Available Endpoints</h2>
                    <div class="endpoint">
                        <strong>System Health:</strong> 
                        <a href="/health">GET /health</a>
                    </div>
                    <div class="endpoint">
                        <strong>API Status:</strong> 
                        <a href="/api/status">GET /api/status</a>
                    </div>
                    {'<div class="endpoint"><strong>Gemini Chat:</strong> <a href="/api/v1/gemini-chat/health">GET /api/v1/gemini-chat/health</a></div>' if GEMINI_AVAILABLE else ''}
                    <div class="endpoint">
                        <strong>API Documentation:</strong> 
                        <a href="/docs">GET /docs</a>
                    </div>
                    <div class="endpoint">
                        <strong>Alternative Docs:</strong> 
                        <a href="/redoc">GET /redoc</a>
                    </div>
                </div>

                <div class="status">
                    <h2>🎯 Quick Actions</h2>
                    {'<div class="endpoint"><strong>Start Gemini Chat:</strong> <a href="/api/v1/gemini-chat/start-session" onclick="startGeminiChat(); return false;">Start New Session</a></div>' if GEMINI_AVAILABLE else ''}
                    <div class="endpoint">
                        <strong>View API Docs:</strong> 
                        <a href="/docs">Interactive API Documentation</a>
                    </div>
                </div>

                <div class="status">
                    <h2>📝 Notes</h2>
                    <p>Dashboard file not found at: <code>{dashboard_path}</code></p>
                    <p>This is the system status page showing available services and endpoints.</p>
                    <p>All API endpoints are functional and can be tested via the documentation.</p>
                </div>
            </div>

            <script>
                async function startGeminiChat() {{
                    try {{
                        const response = await fetch('/api/v1/gemini-chat/start-session', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ context: 'ai_tools_manager' }})
                        }});
                        const data = await response.json();
                        alert('Chat session started! Session ID: ' + data.session_id);
                    }} catch (error) {{
                        alert('Error starting chat session: ' + error.message);
                    }}
                }}
            </script>
        </body>
        </html>
        """)

# Mount static files
try:
    frontend_dir = Path(__file__).parent / "frontend"
    if frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
        print(f"📁 Static files mounted from: {frontend_dir}")
    else:
        print(f"⚠️  Frontend directory not found: {frontend_dir}")
except Exception as e:
    print(f"⚠️  Could not mount static files: {e}")

# API status endpoint
@app.get("/api/status")
async def api_status():
    """Get API status and available endpoints"""
    return {
        "status": "online",
        "version": "2.0.0",
        "services": {
            "gemini_chat": GEMINI_AVAILABLE,
            "admin": ADMIN_AVAILABLE,
            "client": CLIENT_AVAILABLE,
            "telegram": TELEGRAM_AVAILABLE
        },
        "endpoints": {
            "health": "/health",
            "gemini_chat": "/api/v1/gemini-chat/*" if GEMINI_AVAILABLE else None,
            "admin": "/api/v1/admin/*" if ADMIN_AVAILABLE else None,
            "client": "/api/v1/client/*" if CLIENT_AVAILABLE else None,
            "telegram": "/api/v1/telegram/*" if TELEGRAM_AVAILABLE else None,
            "documentation": "/docs"
        },
        "features": {
            "gemini_ai": GEMINI_AVAILABLE,
            "admin_panel": ADMIN_AVAILABLE,
            "client_management": CLIENT_AVAILABLE,
            "telegram_integration": TELEGRAM_AVAILABLE,
            "web_interface": True
        }
    }

if __name__ == "__main__":
    print("🚀 Starting VoiceConnect Pro Complete Web Application...")
    print("📝 Available services:")
    print(f"   - Gemini Chat: {'✅ Available' if GEMINI_AVAILABLE else '❌ Unavailable'}")
    print(f"   - Admin Panel: {'✅ Available' if ADMIN_AVAILABLE else '❌ Unavailable'}")
    print(f"   - Client API: {'✅ Available' if CLIENT_AVAILABLE else '❌ Unavailable'}")
    print(f"   - Telegram: {'✅ Available' if TELEGRAM_AVAILABLE else '❌ Unavailable'}")
    print()
    print("📝 Available endpoints:")
    print("   - GET  /health (System health)")
    print("   - GET  /api/status (API status)")
    if GEMINI_AVAILABLE:
        print("   - POST /api/v1/gemini-chat/* (Gemini Chat)")
    if ADMIN_AVAILABLE:
        print("   - POST /api/v1/admin/* (Admin)")
    if CLIENT_AVAILABLE:
        print("   - POST /api/v1/client/* (Client)")
    if TELEGRAM_AVAILABLE:
        print("   - POST /api/v1/telegram/* (Telegram)")
    print("   - GET  / (Main dashboard)")
    print("   - GET  /docs (API documentation)")
    print()
    print("🌐 Server will be available at:")
    print("   - http://localhost:12000")
    print("   - https://work-1-uojdozitopihokid.prod-runtime.all-hands.dev")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=12000,
        reload=False,
        access_log=True
    )