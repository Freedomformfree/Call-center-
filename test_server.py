#!/usr/bin/env python3
"""
Simple test server for Gemini chat functionality
This server only includes the Gemini chat endpoints for testing.
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Add core-api to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core-api'))

# Import Gemini chat router
from gemini_chat_api import router as gemini_chat_router

# Create FastAPI app
app = FastAPI(
    title="VoiceConnect Pro - Gemini Chat Test Server",
    description="Test server for Gemini AI chat functionality",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Gemini chat router
app.include_router(gemini_chat_router)

# Mount static files (frontend)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "gemini-chat-test-server",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Gemini Chat Test Server...")
    print("📝 Available endpoints:")
    print("   - GET  /health")
    print("   - POST /api/v1/gemini-chat/start-session")
    print("   - POST /api/v1/gemini-chat/send-message")
    print("   - GET  /api/v1/gemini-chat/history/{session_id}")
    print("   - DELETE /api/v1/gemini-chat/session/{session_id}")
    print("   - POST /api/v1/gemini-chat/parse-response")
    print("   - GET  /api/v1/gemini-chat/health")
    print("   - GET  / (Frontend dashboard)")
    print()
    print("🌐 Server will be available at:")
    print("   - http://localhost:12000")
    print("   - https://work-1-uojdozitopihokid.prod-runtime.all-hands.dev")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=12000,
        reload=False
    )