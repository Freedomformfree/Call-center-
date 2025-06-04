"""
Call Webhook API Endpoints
Handles incoming webhooks from VoIP providers
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Dict, Any
import structlog
from real_call_service import handle_incoming_call, update_call_status

logger = structlog.get_logger(__name__)

call_webhook_router = APIRouter(prefix="/api/v1/calls", tags=["Call Webhooks"])

@call_webhook_router.post("/webhook/{call_id}")
async def handle_call_webhook(call_id: str, request: Request):
    """
    Handle call webhook from VoIP provider
    
    This endpoint receives webhooks for call events like:
    - Call initiated
    - Call ringing
    - Call answered
    - Call completed
    """
    try:
        # Get webhook data
        webhook_data = await request.json() if request.headers.get('content-type') == 'application/json' else await request.form()
        
        logger.info("Call webhook received", call_id=call_id, data=webhook_data)
        
        # Extract status from webhook (provider-specific)
        status = None
        details = {}
        
        # SIM800C local GSM webhook format
        if 'sim800c_status' in webhook_data:
            status = webhook_data['sim800c_status'].lower()
            details = {
                'duration': webhook_data.get('duration'),
                'modem_port': webhook_data.get('modem_port'),
                'reason': webhook_data.get('sim800c_status')
            }
        
        # Vonage webhook format
        elif 'status' in webhook_data:
            status = webhook_data['status'].lower()
            details = {
                'duration': webhook_data.get('duration'),
                'reason': webhook_data.get('reason')
            }
        
        if status:
            result = await update_call_status(call_id, status, details)
            if result['success']:
                return {"status": "ok", "message": "Webhook processed"}
            else:
                raise HTTPException(status_code=400, detail=result['error'])
        else:
            logger.warning("Unknown webhook format", data=webhook_data)
            return {"status": "ok", "message": "Webhook received but not processed"}
            
    except Exception as e:
        logger.error("Error processing call webhook", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@call_webhook_router.post("/webhook/{call_id}/status")
async def handle_call_status_webhook(call_id: str, request: Request):
    """Handle call status webhook (SIM800C local GSM specific)"""
    return await handle_call_webhook(call_id, request)

@call_webhook_router.post("/webhook/{call_id}/events")
async def handle_call_events_webhook(call_id: str, request: Request):
    """Handle call events webhook (Vonage specific)"""
    return await handle_call_webhook(call_id, request)

@call_webhook_router.post("/incoming")
async def handle_incoming_call_webhook(request: Request):
    """
    Handle incoming call webhook
    
    This endpoint receives webhooks when someone calls a company number
    """
    try:
        # Get webhook data
        webhook_data = await request.json() if request.headers.get('content-type') == 'application/json' else await request.form()
        
        logger.info("Incoming call webhook received", data=webhook_data)
        
        # Extract caller and called numbers (provider-specific)
        from_number = None
        to_number = None
        
        # SIM800C local GSM format
        if 'from_number' in webhook_data and 'to_number' in webhook_data:
            from_number = webhook_data['from_number']
            to_number = webhook_data['to_number']
        
        # Vonage format
        elif 'from' in webhook_data and 'to' in webhook_data:
            from_number = webhook_data['from']
            to_number = webhook_data['to']
        
        if from_number and to_number:
            result = await handle_incoming_call(from_number, to_number)
            
            if result['success']:
                # Return appropriate response based on provider
                if result['action'] == 'answer':
                    # Return TwiML or NCCO based on provider
                    return generate_call_response(result)
                else:
                    return {"action": "reject"}
            else:
                return {"action": "reject", "reason": result['error']}
        else:
            logger.warning("Missing caller/called numbers in webhook", data=webhook_data)
            return {"action": "reject", "reason": "Invalid webhook data"}
            
    except Exception as e:
        logger.error("Error processing incoming call webhook", error=str(e))
        return {"action": "reject", "reason": str(e)}

def generate_call_response(call_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate appropriate call response based on provider
    
    For SIM800C: Return AT command response
    For Vonage: Return NCCO (Nexmo Call Control Object)
    """
    
    # For now, return a simple response that connects to AI
    # In a real implementation, this would:
    # 1. Connect to Gemini AI with the appropriate prompt
    # 2. Handle speech-to-text and text-to-speech
    # 3. Manage conversation flow
    
    ai_prompt = call_info.get('ai_prompt', '')
    gemini_api_key = call_info.get('gemini_api_key', '')
    
    # Simplified response - in production this would be more complex
    return {
        "action": "talk",
        "text": "Здравствуйте! Добро пожаловать в AI Call Center. Как я могу вам помочь?",
        "voice": "alice",
        "language": "ru-RU",
        "ai_config": {
            "prompt": ai_prompt,
            "api_key": gemini_api_key,
            "call_type": call_info.get('call_type')
        }
    }

@call_webhook_router.get("/test")
async def test_webhook():
    """Test endpoint to verify webhook functionality"""
    return {"status": "ok", "message": "Call webhook API is working"}