"""
Real Phone Call Service Implementation
Supports multiple VoIP providers and real phone call functionality
"""

import os
import asyncio
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import structlog
import httpx
from sqlmodel import Session, select

from database import get_session
from models import Call, CallStatus, Modem, User

logger = structlog.get_logger(__name__)

class CallProvider:
    """Base call provider interface"""
    
    async def initiate_call(self, from_number: str, to_number: str, webhook_url: str) -> Dict[str, Any]:
        """Initiate a phone call"""
        raise NotImplementedError
    
    async def handle_call_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming call webhook"""
        raise NotImplementedError

class SIM800CCallProvider(CallProvider):
    """Local SIM800C GSM module call provider"""
    
    def __init__(self):
        self.available_modems = []
        self._load_available_modems()
    
    def _load_available_modems(self):
        """Load available SIM800C modems from database"""
        try:
            with Session(get_session().bind) as session:
                modems = session.exec(
                    select(Modem).where(Modem.status == "active")
                ).all()
                self.available_modems = [modem.port for modem in modems]
                logger.info(f"Loaded {len(self.available_modems)} active SIM800C modems")
        except Exception as e:
            logger.error("Failed to load modems", error=str(e))
    
    async def initiate_call(self, from_number: str, to_number: str, webhook_url: str) -> Dict[str, Any]:
        """Initiate call via local SIM800C module"""
        try:
            if not self.available_modems:
                return {
                    'success': False,
                    'error': 'No active SIM800C modems available',
                    'provider': 'sim800c_local'
                }
            
            # Use first available modem (can be enhanced with load balancing)
            modem_port = self.available_modems[0]
            
            # Simulate call initiation (replace with actual AT commands)
            call_id = f"sim800c_{datetime.utcnow().timestamp()}"
            
            logger.info(f"Initiating call via SIM800C on {modem_port}: {from_number} -> {to_number}")
            
            return {
                'success': True,
                'call_id': call_id,
                'status': 'initiated',
                'provider': 'sim800c_local',
                'modem_port': modem_port
            }
            
        except Exception as e:
            logger.error("SIM800C call error", error=str(e))
            return {
                'success': False,
                'error': f"SIM800C exception: {str(e)}",
                'provider': 'sim800c_local'
            }
    
    async def handle_call_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SIM800C call status webhook"""
        try:
            call_id = webhook_data.get('call_id')
            status = webhook_data.get('status', 'unknown')
            
            logger.info(f"SIM800C call webhook: {call_id} -> {status}")
            
            return {
                'success': True,
                'call_id': call_id,
                'status': status,
                'provider': 'sim800c_local'
            }
            
        except Exception as e:
            logger.error("SIM800C webhook error", error=str(e))
            return {
                'success': False,
                'error': f"SIM800C webhook exception: {str(e)}",
                'provider': 'sim800c_local'
            }



class VonageCallProvider(CallProvider):
    """Vonage (Nexmo) Voice provider"""
    
    def __init__(self, api_key: str, api_secret: str, application_id: str, private_key: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.application_id = application_id
        self.private_key = private_key
        self.base_url = "https://api.nexmo.com/v1/calls"
    
    async def initiate_call(self, from_number: str, to_number: str, webhook_url: str) -> Dict[str, Any]:
        """Initiate call via Vonage"""
        try:
            # Generate JWT token for authentication
            import jwt
            import time
            
            payload = {
                'iat': int(time.time()),
                'exp': int(time.time()) + 3600,
                'jti': f"call_{int(time.time())}",
                'application_id': self.application_id
            }
            
            token = jwt.encode(payload, self.private_key, algorithm='RS256')
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'to': [{'type': 'phone', 'number': to_number}],
                        'from': {'type': 'phone', 'number': from_number},
                        'answer_url': [webhook_url],
                        'event_url': [f"{webhook_url}/events"]
                    }
                )
                
                if response.status_code == 201:
                    data = response.json()
                    return {
                        'success': True,
                        'call_id': data.get('uuid'),
                        'status': data.get('status'),
                        'provider': 'vonage'
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Vonage error: {response.status_code} - {response.text}",
                        'provider': 'vonage'
                    }
        except Exception as e:
            logger.error("Vonage call error", error=str(e))
            return {
                'success': False,
                'error': f"Vonage exception: {str(e)}",
                'provider': 'vonage'
            }

class DevelopmentCallProvider(CallProvider):
    """Development/testing call provider (simulation)"""
    
    async def initiate_call(self, from_number: str, to_number: str, webhook_url: str) -> Dict[str, Any]:
        """Simulate call initiation for development"""
        logger.info("Development call", from_number=from_number, to_number=to_number)
        return {
            'success': True,
            'call_id': f"dev_call_{datetime.now().timestamp()}",
            'status': 'initiated',
            'provider': 'development'
        }

class RealCallService:
    """Real call service with multiple provider support"""
    
    def __init__(self):
        self.provider = self._initialize_provider()
        self.webhook_base_url = os.getenv('WEBHOOK_BASE_URL', 'https://your-domain.com/api/v1/calls')
    
    def _initialize_provider(self) -> CallProvider:
        """Initialize call provider based on environment variables"""
        
        # Priority 1: Check for local SIM800C modules
        use_local_gsm = os.getenv('USE_LOCAL_GSM', 'true').lower() == 'true'
        if use_local_gsm:
            logger.info("Using local SIM800C GSM modules for calls")
            return SIM800CCallProvider()
        
        # Priority 2: Check for Vonage credentials
        vonage_key = os.getenv('VONAGE_API_KEY')
        vonage_secret = os.getenv('VONAGE_API_SECRET')
        vonage_app_id = os.getenv('VONAGE_APPLICATION_ID')
        vonage_private_key = os.getenv('VONAGE_PRIVATE_KEY')
        
        if vonage_key and vonage_secret and vonage_app_id and vonage_private_key:
            logger.info("Using Vonage Voice provider")
            return VonageCallProvider(vonage_key, vonage_secret, vonage_app_id, vonage_private_key)
        
        # Fallback to development provider
        logger.warning("No call provider configured, using development mode")
        return DevelopmentCallProvider()
    
    async def initiate_consultation_call(self, user_id: str, company_phone: str) -> Dict[str, Any]:
        """
        Initiate a consultation call between user and company AI
        
        Args:
            user_id: User ID requesting consultation
            company_phone: Company phone number to call
            
        Returns:
            Call initiation result
        """
        try:
            with Session(get_session().bind) as session:
                # Get user details
                user = session.get(User, user_id)
                if not user:
                    return {
                        'success': False,
                        'error': 'User not found'
                    }
                
                # Get company modem for the phone number
                stmt = select(Modem).where(Modem.phone_number == company_phone)
                modem = session.exec(stmt).first()
                
                if not modem:
                    return {
                        'success': False,
                        'error': 'Company phone number not found'
                    }
                
                # Create call record
                call = Call(
                    caller_phone=user.phone,
                    called_phone=company_phone,
                    modem_id=modem.id,
                    user_id=user.id,
                    status=CallStatus.INITIATED,
                    call_type='consultation',
                    started_at=datetime.utcnow()
                )
                session.add(call)
                session.commit()
                session.refresh(call)
                
                # Generate webhook URL for this specific call
                webhook_url = f"{self.webhook_base_url}/webhook/{call.id}"
                
                # Initiate call via provider
                result = await self.provider.initiate_call(
                    from_number=company_phone,
                    to_number=user.phone,
                    webhook_url=webhook_url
                )
                
                # Update call record with provider details
                call.external_call_id = result.get('call_id')
                call.provider = result.get('provider')
                
                if result['success']:
                    call.status = CallStatus.RINGING
                    logger.info("Consultation call initiated",
                              user_id=user_id,
                              call_id=call.id,
                              provider=result.get('provider'))
                else:
                    call.status = CallStatus.FAILED
                    call.end_reason = result.get('error')
                    logger.error("Failed to initiate consultation call",
                               user_id=user_id,
                               error=result.get('error'))
                
                session.commit()
                
                return {
                    'success': result['success'],
                    'call_id': str(call.id),
                    'external_call_id': result.get('call_id'),
                    'status': call.status,
                    'provider': result.get('provider'),
                    'error': result.get('error')
                }
                
        except Exception as e:
            logger.error("Error initiating consultation call", error=str(e))
            return {
                'success': False,
                'error': f"Internal error: {str(e)}"
            }
    
    async def handle_incoming_call(self, from_number: str, to_number: str) -> Dict[str, Any]:
        """
        Handle incoming call to company number
        
        Args:
            from_number: Caller's phone number
            to_number: Called company number
            
        Returns:
            Call handling instructions
        """
        try:
            with Session(get_session().bind) as session:
                # Find the modem for this company number
                stmt = select(Modem).where(Modem.phone_number == to_number)
                modem = session.exec(stmt).first()
                
                if not modem:
                    return {
                        'success': False,
                        'error': 'Company number not found',
                        'action': 'reject'
                    }
                
                # Check if caller is a registered user
                stmt = select(User).where(User.phone == from_number)
                user = session.exec(stmt).first()
                
                # Create call record
                call = Call(
                    caller_phone=from_number,
                    called_phone=to_number,
                    modem_id=modem.id,
                    user_id=user.id if user else None,
                    status=CallStatus.RINGING,
                    call_type='incoming',
                    started_at=datetime.utcnow()
                )
                session.add(call)
                session.commit()
                session.refresh(call)
                
                # Determine call handling based on user status and modem configuration
                if user and modem.assigned_user_id == user.id:
                    # This is the user's assigned number - use their custom prompt
                    ai_prompt = self._get_user_custom_prompt(user.id, session)
                    call_type = 'client_custom'
                else:
                    # Use company consultation prompt
                    ai_prompt = self._get_company_consultation_prompt()
                    call_type = 'company_consultation'
                
                call.call_type = call_type
                session.commit()
                
                logger.info("Incoming call handled",
                          from_number=from_number,
                          to_number=to_number,
                          call_id=call.id,
                          call_type=call_type)
                
                return {
                    'success': True,
                    'call_id': str(call.id),
                    'action': 'answer',
                    'ai_prompt': ai_prompt,
                    'gemini_api_key': modem.gemini_api_key,
                    'call_type': call_type
                }
                
        except Exception as e:
            logger.error("Error handling incoming call", error=str(e))
            return {
                'success': False,
                'error': f"Internal error: {str(e)}",
                'action': 'reject'
            }
    
    def _get_company_consultation_prompt(self) -> str:
        """Get the company consultation AI prompt"""
        return """
        You are an AI Business Automation Consultant for our Call Center service. Your mission is to help clients automate their business processes.

        CONSULTATION FLOW (30 minutes):
        
        1. WELCOME & DISCOVERY (5 minutes)
           - Greet warmly and introduce our AI automation services
           - Ask about their business type (hotel, restaurant, retail, healthcare, beauty salon, etc.)
           - Understand their current challenges and pain points
           
        2. BUSINESS ANALYSIS (10 minutes)
           - Identify specific processes they want to automate
           - Ask about their customer interaction volume
           - Understand their current tools and systems
           - Discover time-consuming manual tasks
           
        3. SOLUTION PRESENTATION (10 minutes)
           Based on their business type, present relevant automation tools:
           
           HOTELS: Room booking, guest communication, check-in/out automation, review management
           RESTAURANTS: Order taking, delivery coordination, reservation management, customer feedback
           RETAIL: Inventory alerts, customer follow-up, order processing, sales analytics
           HEALTHCARE: Appointment scheduling, patient reminders, prescription notifications
           BEAUTY SALONS: Booking management, client reminders, service upselling
           EDUCATION: Course enrollment, student communication, payment reminders
           REAL ESTATE: Lead qualification, property inquiries, viewing scheduling
           CONSULTING: Client onboarding, meeting scheduling, follow-up automation
           
        4. CUSTOMIZATION (3 minutes)
           - Explain how tools can be customized for their specific needs
           - Mention integration with their existing systems
           - Highlight time and cost savings
           
        5. SUBSCRIPTION OFFER (2 minutes)
           - Present our $20/month AI Assistant plan
           - Explain included features based on their needs
           - Offer to create a custom automation workflow
           
        IMPORTANT GUIDELINES:
        - Be consultative, not pushy
        - Focus on solving their specific problems
        - Use examples relevant to their business type
        - Collect detailed information about their needs
        - End with clear next steps if they're interested
        - Always respect the 30-minute time limit
        
        Remember: Your goal is to understand their business deeply and recommend the most valuable automation tools for their specific situation.
        """
    
    def _get_user_custom_prompt(self, user_id: str, session: Session) -> str:
        """Get user's custom AI prompt based on their subscription"""
        # This would fetch the user's custom configuration
        # For now, return a default prompt
        return """
        Вы - персональный AI-помощник клиента. Отвечайте на звонки согласно 
        настройкам клиента и помогайте решать задачи его бизнеса.
        """
    
    async def update_call_status(self, call_id: str, status: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update call status from webhook"""
        try:
            with Session(get_session().bind) as session:
                call = session.get(Call, call_id)
                if not call:
                    return {'success': False, 'error': 'Call not found'}
                
                # Map provider status to our status
                status_mapping = {
                    'initiated': CallStatus.INITIATED,
                    'ringing': CallStatus.RINGING,
                    'answered': CallStatus.ACTIVE,
                    'in-progress': CallStatus.ACTIVE,
                    'completed': CallStatus.COMPLETED,
                    'busy': CallStatus.FAILED,
                    'no-answer': CallStatus.FAILED,
                    'failed': CallStatus.FAILED,
                    'cancelled': CallStatus.FAILED
                }
                
                old_status = call.status
                call.status = status_mapping.get(status, CallStatus.FAILED)
                
                if call.status == CallStatus.ACTIVE and old_status != CallStatus.ACTIVE:
                    call.answered_at = datetime.utcnow()
                elif call.status in [CallStatus.COMPLETED, CallStatus.FAILED]:
                    call.ended_at = datetime.utcnow()
                    if details:
                        call.duration_seconds = details.get('duration')
                        call.end_reason = details.get('reason')
                
                session.commit()
                
                logger.info("Call status updated",
                          call_id=call_id,
                          old_status=old_status,
                          new_status=call.status)
                
                return {'success': True}
                
        except Exception as e:
            logger.error("Error updating call status", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def process_consultation_completion(
        self, 
        call_id: str, 
        conversation_transcript: str,
        call_duration_minutes: int
    ) -> Dict[str, Any]:
        """
        Process completed consultation call and trigger analysis.
        
        Args:
            call_id: Call ID
            conversation_transcript: Full conversation transcript
            call_duration_minutes: Duration of the call in minutes
            
        Returns:
            Analysis results and subscription offer
        """
        try:
            with Session(get_session().bind) as session:
                # Get call details
                call = session.get(Call, call_id)
                if not call:
                    return {'success': False, 'error': 'Call not found'}
                
                # Check if this was a consultation call
                if call.call_type != 'consultation':
                    return {'success': False, 'error': 'Not a consultation call'}
                
                # Get user from temporary phone assignment
                from models import TemporaryPhoneAssignment
                from sqlmodel import select
                
                assignment = session.exec(
                    select(TemporaryPhoneAssignment).where(
                        TemporaryPhoneAssignment.phone_number == call.to_number,
                        TemporaryPhoneAssignment.is_active == True
                    )
                ).first()
                
                if not assignment:
                    return {'success': False, 'error': 'No active phone assignment found'}
                
                user_id = str(assignment.user_id)
                
                # Import and use consultation analysis service
                from consultation_analysis_service import get_consultation_analysis_service
                analysis_service = get_consultation_analysis_service()
                
                if not analysis_service:
                    logger.error("Consultation analysis service not available")
                    return {'success': False, 'error': 'Analysis service unavailable'}
                
                # Analyze the consultation
                analysis_result = await analysis_service.analyze_consultation(
                    user_id=user_id,
                    conversation_transcript=conversation_transcript,
                    call_duration_minutes=call_duration_minutes
                )
                
                if analysis_result['success']:
                    # Update call with analysis results
                    call.conversation_summary = analysis_result['analysis']['summary']
                    call.ai_analysis_data = json.dumps(analysis_result['analysis'])
                    session.commit()
                    
                    logger.info("Consultation analysis completed", 
                               call_id=call_id, 
                               user_id=user_id,
                               business_type=analysis_result['analysis']['business_type']['name'])
                    
                    return {
                        'success': True,
                        'analysis': analysis_result['analysis'],
                        'subscription_offer': {
                            'monthly_price': analysis_result['analysis']['pricing']['monthly_price'],
                            'recommended_tools': analysis_result['analysis']['recommended_tools'],
                            'business_type': analysis_result['analysis']['business_type']['name']
                        }
                    }
                else:
                    logger.error("Consultation analysis failed", error=analysis_result.get('error'))
                    return analysis_result
                
        except Exception as e:
            logger.error("Error processing consultation completion", error=str(e))
            return {'success': False, 'error': str(e)}

# Global call service instance
real_call_service = RealCallService()

# Convenience functions
async def initiate_consultation_call(user_id: str, company_phone: str) -> Dict[str, Any]:
    """Initiate consultation call"""
    return await real_call_service.initiate_consultation_call(user_id, company_phone)

async def handle_incoming_call(from_number: str, to_number: str) -> Dict[str, Any]:
    """Handle incoming call"""
    return await real_call_service.handle_incoming_call(from_number, to_number)

async def update_call_status(call_id: str, status: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
    """Update call status"""
    return await real_call_service.update_call_status(call_id, status, details)

async def process_consultation_completion(
    call_id: str, 
    conversation_transcript: str, 
    call_duration_minutes: int
) -> Dict[str, Any]:
    """Process consultation completion"""
    return await real_call_service.process_consultation_completion(
        call_id, conversation_transcript, call_duration_minutes
    )