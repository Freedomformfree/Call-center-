#!/usr/bin/env python3
"""
VoiceConnect Pro - Main Web Application
Web-only version without hardware dependencies for testing
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer
import uvicorn
from contextlib import asynccontextmanager

# Import API routers
from auth_api import router as auth_router
from ai_tools_api import router as ai_tools_router
from gemini_chat_api import router as gemini_chat_router

# Import services
from ai_tools_service import ai_tools_service

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    print("🚀 Starting VoiceConnect Pro Web Application...")
    print("📝 Initializing services...")
    
    # Initialize AI tools service
    try:
        await ai_tools_service.initialize()
        print("✅ AI Tools service initialized")
    except Exception as e:
        print(f"⚠️  AI Tools service initialization warning: {e}")
    
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
        "service": "voiceconnect-pro-web",
        "version": "2.0.0",
        "components": {
            "api": "online",
            "ai_tools": "online",
            "gemini_chat": "online",
            "frontend": "online"
        }
    }

# Include API routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(ai_tools_router, prefix="/api/v1/ai-tools", tags=["AI Tools"])
app.include_router(gemini_chat_router, prefix="/api/v1/gemini-chat", tags=["Gemini Chat"])

# Serve the main dashboard
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard"""
    try:
        dashboard_path = current_dir.parent / "frontend" / "dashboard.html"
        with open(dashboard_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <head>
                <title>VoiceConnect Pro - Dashboard Not Found</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .error { color: #e74c3c; }
                    .info { color: #3498db; }
                    ul { margin: 20px 0; }
                    li { margin: 5px 0; }
                </style>
            </head>
            <body>
                <h1>VoiceConnect Pro</h1>
                <p class="error">Dashboard file not found at expected location.</p>
                <p class="info">Available API endpoints:</p>
                <ul>
                    <li><a href="/health">System Health Check</a></li>
                    <li><a href="/api/v1/gemini-chat/health">Gemini Chat Health</a></li>
                    <li><a href="/docs">API Documentation</a></li>
                    <li><a href="/redoc">API Documentation (ReDoc)</a></li>
                </ul>
                <p>Expected dashboard location: <code>{dashboard_path}</code></p>
            </body>
        </html>
        """.format(dashboard_path=dashboard_path))

# Mount static files
try:
    frontend_dir = current_dir.parent / "frontend"
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
        "endpoints": {
            "health": "/health",
            "auth": "/api/v1/auth/*",
            "ai_tools": "/api/v1/ai-tools/*",
            "gemini_chat": "/api/v1/gemini-chat/*",
            "documentation": "/docs"
        },
        "features": {
            "gemini_ai": True,
            "ai_tools": True,
            "authentication": True,
            "web_interface": True
        }
    }

if __name__ == "__main__":
    print("🚀 Starting VoiceConnect Pro Web Application...")
    print("📝 Available endpoints:")
    print("   - GET  /health (System health)")
    print("   - GET  /api/status (API status)")
    print("   - POST /api/v1/auth/* (Authentication)")
    print("   - POST /api/v1/ai-tools/* (AI Tools)")
    print("   - POST /api/v1/gemini-chat/* (Gemini Chat)")
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