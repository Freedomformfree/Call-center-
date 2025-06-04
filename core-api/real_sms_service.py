"""
Real SMS Service Implementation
Supports multiple SMS providers: SMS.ru, SMSC.ru, Local GSM modules
"""

import os
import random
import string
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import structlog
import httpx
from sqlmodel import Session, select

from database import get_session
from models import SMSMessage, SMSStatus
from local_gsm_sms_service import LocalGSMSMSService

logger = structlog.get_logger(__name__)

class SMSProvider:
    """Base SMS provider interface"""
    
    async def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS and return result"""
        raise NotImplementedError

class SIM800CSMSProvider(SMSProvider):
    """Local SIM800C GSM module SMS provider"""
    
    def __init__(self):
        self.gsm_service = LocalGSMSMSService()
    
    async def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS via local SIM800C module"""
        try:
            result = await self.gsm_service.send_sms(phone_number, message)
            
            if result.get('success'):
                return {
                    'success': True,
                    'message_id': result.get('message_id'),
                    'status': 'sent',
                    'provider': 'sim800c_local'
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown SIM800C error'),
                    'provider': 'sim800c_local'
                }
        except Exception as e:
            logger.error("SIM800C SMS error", error=str(e))
            return {
                'success': False,
                'error': f"SIM800C exception: {str(e)}",
                'provider': 'sim800c_local'
            }


class SMSRuProvider(SMSProvider):
    """SMS.ru provider"""
    
    def __init__(self, api_id: str):
        self.api_id = api_id
        self.base_url = "https://sms.ru/sms/send"
    
    async def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS via SMS.ru"""
        try:
            # Clean phone number (remove + and spaces)
            clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    data={
                        'api_id': self.api_id,
                        'to': clean_phone,
                        'msg': message,
                        'json': 1
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'OK':
                        return {
                            'success': True,
                            'message_id': data.get('sms', {}).get(clean_phone, {}).get('sms_id'),
                            'status': 'sent',
                            'provider': 'sms.ru'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"SMS.ru error: {data.get('status_text', 'Unknown error')}",
                            'provider': 'sms.ru'
                        }
                else:
                    return {
                        'success': False,
                        'error': f"SMS.ru HTTP error: {response.status_code}",
                        'provider': 'sms.ru'
                    }
        except Exception as e:
            logger.error("SMS.ru error", error=str(e))
            return {
                'success': False,
                'error': f"SMS.ru exception: {str(e)}",
                'provider': 'sms.ru'
            }

class SMSCRuProvider(SMSProvider):
    """SMSC.ru provider"""
    
    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
        self.base_url = "https://smsc.ru/sys/send.php"
    
    async def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS via SMSC.ru"""
        try:
            # Clean phone number
            clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    data={
                        'login': self.login,
                        'psw': self.password,
                        'phones': clean_phone,
                        'mes': message,
                        'fmt': 3  # JSON format
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'id' in data:
                        return {
                            'success': True,
                            'message_id': str(data['id']),
                            'status': 'sent',
                            'provider': 'smsc.ru'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"SMSC.ru error: {data.get('error_code', 'Unknown error')}",
                            'provider': 'smsc.ru'
                        }
                else:
                    return {
                        'success': False,
                        'error': f"SMSC.ru HTTP error: {response.status_code}",
                        'provider': 'smsc.ru'
                    }
        except Exception as e:
            logger.error("SMSC.ru error", error=str(e))
            return {
                'success': False,
                'error': f"SMSC.ru exception: {str(e)}",
                'provider': 'smsc.ru'
            }

class DevelopmentSMSProvider(SMSProvider):
    """Development/testing SMS provider (simulation)"""
    
    async def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Simulate SMS sending for development"""
        logger.info("Development SMS", phone=phone_number, message=message)
        return {
            'success': True,
            'message_id': f"dev_{random.randint(100000, 999999)}",
            'status': 'sent',
            'provider': 'development'
        }

class RealSMSService:
    """Real SMS service with multiple provider support"""
    
    def __init__(self):
        self.provider = self._initialize_provider()
    
    def _initialize_provider(self) -> SMSProvider:
        """Initialize SMS provider based on environment variables"""
        
        # Priority 1: Check for local SIM800C modules
        use_local_gsm = os.getenv('USE_LOCAL_GSM', 'true').lower() == 'true'
        if use_local_gsm:
            logger.info("Using local SIM800C GSM modules for SMS")
            return SIM800CSMSProvider()
        
        # Priority 2: Check for SMS.ru credentials
        sms_ru_api_id = os.getenv('SMS_RU_API_ID')
        if sms_ru_api_id:
            logger.info("Using SMS.ru provider")
            return SMSRuProvider(sms_ru_api_id)
        
        # Priority 3: Check for SMSC.ru credentials
        smsc_login = os.getenv('SMSC_LOGIN')
        smsc_password = os.getenv('SMSC_PASSWORD')
        if smsc_login and smsc_password:
            logger.info("Using SMSC.ru provider")
            return SMSCRuProvider(smsc_login, smsc_password)
        
        # Fallback to development provider
        logger.warning("No SMS provider configured, using development mode")
        return DevelopmentSMSProvider()
    
    def generate_verification_code(self) -> str:
        """Generate 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=6))
    
    async def send_verification_sms(self, phone_number: str) -> Dict[str, Any]:
        """Send verification SMS and store in database"""
        
        # Generate verification code
        verification_code = self.generate_verification_code()
        
        # Create SMS message
        message = f"Ваш код подтверждения для AI Call Center: {verification_code}. Код действителен 10 минут."
        
        # Send SMS
        result = await self.provider.send_sms(phone_number, message)
        
        # Store in database
        with Session(get_session().bind) as session:
            sms_message = SMSMessage(
                phone_number=phone_number,
                message=message,
                verification_code=verification_code,
                status=SMSStatus.SENT if result['success'] else SMSStatus.PENDING,
                provider=result.get('provider', 'unknown'),
                external_id=result.get('message_id'),
                expires_at=datetime.utcnow() + timedelta(minutes=10)
            )
            session.add(sms_message)
            session.commit()
            session.refresh(sms_message)
            
            logger.info(
                "SMS verification sent",
                phone=phone_number,
                code=verification_code,
                success=result['success'],
                provider=result.get('provider')
            )
            
            return {
                'success': result['success'],
                'verification_code': verification_code,  # For development/testing
                'message_id': sms_message.id,
                'provider': result.get('provider'),
                'error': result.get('error')
            }
    
    async def verify_code(self, phone_number: str, code: str) -> Dict[str, Any]:
        """Verify SMS code"""
        
        with Session(get_session().bind) as session:
            # Find the most recent SMS for this phone number
            stmt = select(SMSMessage).where(
                SMSMessage.phone_number == phone_number,
                SMSMessage.verification_code == code,
                SMSMessage.expires_at > datetime.utcnow(),
                SMSMessage.verified_at.is_(None)
            ).order_by(SMSMessage.created_at.desc())
            
            sms_message = session.exec(stmt).first()
            
            if not sms_message:
                return {
                    'success': False,
                    'error': 'Неверный или истекший код подтверждения'
                }
            
            # Mark as verified
            sms_message.verified_at = datetime.utcnow()
            sms_message.status = SMSStatus.DELIVERED
            session.add(sms_message)
            session.commit()
            
            logger.info("SMS code verified", phone=phone_number, code=code)
            
            return {
                'success': True,
                'message': 'Код подтверждения успешно проверен'
            }
    
    async def send_notification_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send notification SMS"""
        
        result = await self.provider.send_sms(phone_number, message)
        
        # Store in database
        with Session(get_session().bind) as session:
            sms_message = SMSMessage(
                phone_number=phone_number,
                message=message,
                status=SMSStatus.SENT if result['success'] else SMSStatus.PENDING,
                provider=result.get('provider', 'unknown'),
                external_id=result.get('message_id')
            )
            session.add(sms_message)
            session.commit()
            
            logger.info(
                "Notification SMS sent",
                phone=phone_number,
                success=result['success'],
                provider=result.get('provider')
            )
            
            return result

# Global SMS service instance
real_sms_service = RealSMSService()

# Convenience functions
async def send_verification_sms(phone_number: str) -> Dict[str, Any]:
    """Send verification SMS"""
    return await real_sms_service.send_verification_sms(phone_number)

async def verify_sms_code(phone_number: str, code: str) -> Dict[str, Any]:
    """Verify SMS code"""
    return await real_sms_service.verify_code(phone_number, code)

async def send_notification_sms(phone_number: str, message: str) -> Dict[str, Any]:
    """Send notification SMS"""
    return await real_sms_service.send_notification_sms(phone_number, message)