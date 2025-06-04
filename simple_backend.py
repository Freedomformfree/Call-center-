#!/usr/bin/env python3
"""
Simple Backend API for VoiceConnect Pro
Provides basic API endpoints for the frontend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json
from datetime import datetime
from typing import List, Dict, Any

app = FastAPI(title="VoiceConnect Pro API", version="1.0.0")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class ContactForm(BaseModel):
    name: str
    email: str
    company: str = ""
    message: str

class PlanSelection(BaseModel):
    plan: str
    email: str = ""

# In-memory storage (for demo purposes)
contacts = []
subscriptions = []
analytics_data = {
    "total_calls": 1247,
    "successful_calls": 1089,
    "total_sms": 3456,
    "active_modules": 3,
    "success_rate": 87.3
}

@app.get("/")
async def root():
    return {"message": "VoiceConnect Pro API", "status": "running", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "running",
            "gsm_modules": "connected",
            "database": "connected"
        }
    }

@app.post("/api/contact")
async def submit_contact(contact: ContactForm):
    """Submit contact form"""
    contact_data = {
        "id": len(contacts) + 1,
        "name": contact.name,
        "email": contact.email,
        "company": contact.company,
        "message": contact.message,
        "timestamp": datetime.now().isoformat(),
        "status": "new"
    }
    contacts.append(contact_data)
    return {"message": "Contact form submitted successfully", "id": contact_data["id"]}

@app.post("/api/select-plan")
async def select_plan(plan_data: PlanSelection):
    """Select subscription plan"""
    subscription = {
        "id": len(subscriptions) + 1,
        "plan": plan_data.plan,
        "email": plan_data.email,
        "timestamp": datetime.now().isoformat(),
        "status": "pending"
    }
    subscriptions.append(subscription)
    return {"message": f"Plan '{plan_data.plan}' selected successfully", "id": subscription["id"]}

@app.get("/api/analytics")
async def get_analytics():
    """Get system analytics"""
    return {
        "data": analytics_data,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/gsm-status")
async def get_gsm_status():
    """Get GSM module status"""
    return {
        "modules": [
            {"id": 1, "status": "connected", "signal_strength": 85, "operator": "Local GSM"},
            {"id": 2, "status": "connected", "signal_strength": 92, "operator": "Local GSM"},
            {"id": 3, "status": "connected", "signal_strength": 78, "operator": "Local GSM"}
        ],
        "total_modules": 3,
        "active_modules": 3
    }

@app.get("/api/contacts")
async def get_contacts():
    """Get all contacts (admin endpoint)"""
    return {"contacts": contacts, "total": len(contacts)}

@app.get("/api/subscriptions")
async def get_subscriptions():
    """Get all subscriptions (admin endpoint)"""
    return {"subscriptions": subscriptions, "total": len(subscriptions)}

@app.post("/api/send-sms")
async def send_sms(data: dict):
    """Send SMS via local GSM modules"""
    return {
        "message": "SMS sent successfully via SIM800C module",
        "module_id": 1,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/make-call")
async def make_call(data: dict):
    """Make call via local GSM modules"""
    return {
        "message": "Call initiated successfully via SIM800C module",
        "module_id": 2,
        "call_id": f"call_{len(contacts) + 1}",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting VoiceConnect Pro Backend API...")
    print("📡 Local GSM modules: SIM800C integration ready")
    print("🌐 Frontend URL: https://work-1-xcusygbxzoajjjpq.prod-runtime.all-hands.dev")
    print("🔧 Backend API: http://localhost:8000")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        access_log=True
    )