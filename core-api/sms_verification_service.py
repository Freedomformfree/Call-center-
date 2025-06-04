"""
SMS Verification Service with Local SIM800C Integration

This service provides SMS-based verification using local SIM800C GSM modules
for secure user authentication and phone number verification.
"""

import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import structlog
from sqlmodel import Session, select
from models import User, SMSVerification
from hardware.sim800c_manager import SIM800CManager

logger = structlog.get_logger(__name__)


class SMSVerificationService:
    """
    SMS verification service using local SIM800C GSM modules.
    
    Provides secure phone number verification with OTP codes
    sent via local GSM hardware instead of external services.
    """
    
    def __init__(self, sim800c_manager: SIM800CManager):
        """
        Initialize SMS verification service.
        
        Args:
            sim800c_manager: SIM800C hardware manager instance
        """
        self.sim800c_manager = sim800c_manager
        self.verification_codes: Dict[str, Dict] = {}
        self.code_expiry_minutes = 5
        self.max_attempts = 3
        
    async def send_verification_code(
        self, 
        phone_number: str, 
        session: Session,
        purpose: str = "registration"
    ) -> Tuple[bool, str]:
        """
        Send SMS verification code to phone number.
        
        Args:
            phone_number: Target phone number
            session: Database session
            purpose: Verification purpose (registration, login, etc.)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Clean phone number
            clean_phone = self._clean_phone_number(phone_number)
            
            # Check rate limiting
            if not self._check_rate_limit(clean_phone):
                return False, "Too many verification attempts. Please wait."
            
            # Generate verification code
            verification_code = self._generate_verification_code()
            
            # Create SMS message
            message = self._create_verification_message(verification_code, purpose)
            
            # Send SMS via SIM800C
            sms_result = await self._send_sms_via_sim800c(clean_phone, message)
            
            if sms_result["success"]:
                # Store verification code
                await self._store_verification_code(
                    clean_phone, 
                    verification_code, 
                    purpose,
                    session
                )
                
                logger.info(
                    "SMS verification code sent",
                    phone=clean_phone,
                    purpose=purpose,
                    module=sms_result.get("module", "unknown")
                )
                
                return True, "Verification code sent successfully"
            else:
                logger.error(
                    "Failed to send SMS",
                    phone=clean_phone,
                    error=sms_result.get("error", "Unknown error")
                )
                return False, "Failed to send verification code"
                
        except Exception as e:
            logger.error("SMS verification send failed", error=str(e))
            return False, "Verification service temporarily unavailable"
    
    async def verify_code(
        self, 
        phone_number: str, 
        code: str, 
        session: Session,
        purpose: str = "registration"
    ) -> Tuple[bool, str]:
        """
        Verify SMS code for phone number.
        
        Args:
            phone_number: Phone number to verify
            code: Verification code entered by user
            session: Database session
            purpose: Verification purpose
            
        Returns:
            Tuple of (success, message)
        """
        try:
            clean_phone = self._clean_phone_number(phone_number)
            
            # Get stored verification
            verification = session.exec(
                select(SMSVerification).where(
                    SMSVerification.phone_number == clean_phone,
                    SMSVerification.purpose == purpose,
                    SMSVerification.is_verified == False,
                    SMSVerification.expires_at > datetime.utcnow()
                ).order_by(SMSVerification.created_at.desc())
            ).first()
            
            if not verification:
                return False, "No valid verification code found"
            
            # Check attempts
            if verification.attempts >= self.max_attempts:
                verification.is_expired = True
                session.commit()
                return False, "Maximum verification attempts exceeded"
            
            # Increment attempts
            verification.attempts += 1
            
            # Verify code
            if verification.code == code:
                verification.is_verified = True
                verification.verified_at = datetime.utcnow()
                session.commit()
                
                logger.info(
                    "SMS verification successful",
                    phone=clean_phone,
                    purpose=purpose
                )
                
                return True, "Phone number verified successfully"
            else:
                session.commit()
                remaining_attempts = self.max_attempts - verification.attempts
                
                if remaining_attempts > 0:
                    return False, f"Invalid code. {remaining_attempts} attempts remaining"
                else:
                    verification.is_expired = True
                    session.commit()
                    return False, "Invalid code. Maximum attempts exceeded"
                    
        except Exception as e:
            logger.error("SMS verification failed", error=str(e))
            return False, "Verification failed"
    
    async def _send_sms_via_sim800c(self, phone_number: str, message: str) -> Dict:
        """
        Send SMS using SIM800C GSM modules.
        
        Args:
            phone_number: Target phone number
            message: SMS message content
            
        Returns:
            Result dictionary with success status
        """
        try:
            # Try to send via available SIM800C modules
            for module_name, module in self.sim800c_manager.modules.items():
                if module.is_connected and module.signal_strength > 10:
                    try:
                        result = await module.send_sms(phone_number, message)
                        if result["success"]:
                            return {
                                "success": True,
                                "module": module_name,
                                "message_id": result.get("message_id")
                            }
                    except Exception as e:
                        logger.warning(
                            "SMS send failed on module",
                            module=module_name,
                            error=str(e)
                        )
                        continue
            
            # If all modules failed
            return {
                "success": False,
                "error": "No available GSM modules"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_verification_code(self) -> str:
        """Generate 6-digit verification code."""
        return f"{random.randint(100000, 999999)}"
    
    def _create_verification_message(self, code: str, purpose: str) -> str:
        """
        Create SMS verification message.
        
        Args:
            code: Verification code
            purpose: Verification purpose
            
        Returns:
            SMS message text
        """
        purpose_text = {
            "registration": "account registration",
            "login": "login verification",
            "phone_change": "phone number change",
            "password_reset": "password reset"
        }.get(purpose, "verification")
        
        return (
            f"🤖 VoiceConnect Pro\n"
            f"Your verification code for {purpose_text}: {code}\n"
            f"Valid for 5 minutes. Do not share this code."
        )
    
    def _clean_phone_number(self, phone_number: str) -> str:
        """Clean and format phone number."""
        # Remove all non-digit characters except +
        cleaned = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # Add + if not present and starts with country code
        if not cleaned.startswith('+') and len(cleaned) >= 10:
            if cleaned.startswith('998'):  # Uzbekistan
                cleaned = '+' + cleaned
            elif cleaned.startswith('1') and len(cleaned) == 11:  # US/Canada
                cleaned = '+' + cleaned
            elif len(cleaned) >= 10:
                cleaned = '+' + cleaned
        
        return cleaned
    
    def _check_rate_limit(self, phone_number: str) -> bool:
        """
        Check if phone number is rate limited.
        
        Args:
            phone_number: Phone number to check
            
        Returns:
            True if allowed to send SMS
        """
        now = time.time()
        
        # Clean old entries
        self.verification_codes = {
            phone: data for phone, data in self.verification_codes.items()
            if now - data.get("last_sent", 0) < 300  # 5 minutes
        }
        
        # Check rate limit (max 3 SMS per 5 minutes per phone)
        phone_data = self.verification_codes.get(phone_number, {})
        last_sent = phone_data.get("last_sent", 0)
        count = phone_data.get("count", 0)
        
        if now - last_sent < 60:  # 1 minute between SMS
            return False
        
        if count >= 3 and now - phone_data.get("first_sent", 0) < 300:
            return False
        
        return True
    
    async def _store_verification_code(
        self, 
        phone_number: str, 
        code: str, 
        purpose: str,
        session: Session
    ):
        """
        Store verification code in database.
        
        Args:
            phone_number: Phone number
            code: Verification code
            purpose: Verification purpose
            session: Database session
        """
        # Store in memory for rate limiting
        now = time.time()
        if phone_number not in self.verification_codes:
            self.verification_codes[phone_number] = {
                "first_sent": now,
                "count": 0
            }
        
        self.verification_codes[phone_number].update({
            "last_sent": now,
            "count": self.verification_codes[phone_number]["count"] + 1
        })
        
        # Store in database
        verification = SMSVerification(
            phone_number=phone_number,
            code=code,
            purpose=purpose,
            expires_at=datetime.utcnow() + timedelta(minutes=self.code_expiry_minutes),
            attempts=0,
            is_verified=False,
            is_expired=False
        )
        
        session.add(verification)
        session.commit()
    
    async def cleanup_expired_codes(self, session: Session):
        """Clean up expired verification codes."""
        try:
            expired_time = datetime.utcnow() - timedelta(hours=1)
            
            # Mark expired codes
            expired_verifications = session.exec(
                select(SMSVerification).where(
                    SMSVerification.expires_at < datetime.utcnow(),
                    SMSVerification.is_expired == False
                )
            ).all()
            
            for verification in expired_verifications:
                verification.is_expired = True
            
            session.commit()
            
            logger.info(f"Cleaned up {len(expired_verifications)} expired verification codes")
            
        except Exception as e:
            logger.error("Failed to cleanup expired codes", error=str(e))


# Dependency injection
_sms_verification_service: Optional[SMSVerificationService] = None

def get_sms_verification_service() -> SMSVerificationService:
    """Get SMS verification service instance."""
    global _sms_verification_service
    if _sms_verification_service is None:
        from hardware.sim800c_manager import get_sim800c_manager
        sim800c_manager = get_sim800c_manager()
        _sms_verification_service = SMSVerificationService(sim800c_manager)
    return _sms_verification_service