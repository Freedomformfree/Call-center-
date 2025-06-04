"""
Secure Authentication API with SMS Verification

This module provides secure authentication endpoints with SMS verification
using local SIM800C GSM modules for phone number verification.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from sqlmodel import Session, select
from pydantic import BaseModel, EmailStr
import structlog

from database import get_session
from models import User, UserRole, SMSVerification
from auth import get_auth_manager, AuthManager
from sms_verification_service import get_sms_verification_service, SMSVerificationService
from client_api import get_client_registration_service
from client_registration_service import ClientRegistrationService

logger = structlog.get_logger(__name__)
security = HTTPBearer()

# Create router
secure_auth_router = APIRouter(prefix="/api/v1/secure-auth", tags=["Secure Authentication"])


# Request/Response Models
class SendCodeRequest(BaseModel):
    phone_number: str
    purpose: str = "login"  # login, registration, password_reset


class SendCodeResponse(BaseModel):
    success: bool
    message: str
    phone_number: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone_number: str
    sms_code: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    phone_number: str
    sms_code: str


class AuthResponse(BaseModel):
    success: bool
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user_id: Optional[str] = None
    email: Optional[str] = None
    message: str
    error: Optional[str] = None


class VerifyCodeRequest(BaseModel):
    phone_number: str
    code: str
    purpose: str = "login"


class VerifyCodeResponse(BaseModel):
    success: bool
    message: str
    verified: bool


@secure_auth_router.post("/send-verification-code", response_model=SendCodeResponse)
async def send_verification_code(
    request: SendCodeRequest,
    sms_service: SMSVerificationService = Depends(get_sms_verification_service),
    session: Session = Depends(get_session)
):
    """
    Send SMS verification code to phone number.
    
    Supports multiple purposes: login, registration, password_reset
    """
    try:
        success, message = await sms_service.send_verification_code(
            request.phone_number, 
            session, 
            purpose=request.purpose
        )
        
        if success:
            return SendCodeResponse(
                success=True,
                message=message,
                phone_number=request.phone_number
            )
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to send verification code", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to send verification code")


@secure_auth_router.post("/verify-code", response_model=VerifyCodeResponse)
async def verify_code(
    request: VerifyCodeRequest,
    sms_service: SMSVerificationService = Depends(get_sms_verification_service),
    session: Session = Depends(get_session)
):
    """
    Verify SMS code for phone number.
    
    Used to validate SMS codes before proceeding with authentication.
    """
    try:
        success, message = await sms_service.verify_code(
            request.phone_number,
            request.code,
            session,
            purpose=request.purpose
        )
        
        return VerifyCodeResponse(
            success=True,
            message=message,
            verified=success
        )
        
    except Exception as e:
        logger.error("Failed to verify code", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to verify code")


@secure_auth_router.post("/register", response_model=AuthResponse)
async def register_user(
    request: RegisterRequest,
    auth_manager: AuthManager = Depends(get_auth_manager),
    sms_service: SMSVerificationService = Depends(get_sms_verification_service),
    session: Session = Depends(get_session)
):
    """
    Register new user with SMS verification.
    
    Requires valid SMS verification code before creating account.
    """
    try:
        # Verify SMS code first
        verification_success, verification_message = await sms_service.verify_code(
            request.phone_number, 
            request.sms_code, 
            session, 
            purpose="registration"
        )
        
        if not verification_success:
            return AuthResponse(
                success=False,
                message=verification_message,
                error="SMS_VERIFICATION_FAILED"
            )

        # Check if user already exists
        existing_user = session.exec(
            select(User).where(User.email == request.email)
        ).first()
        
        if existing_user:
            return AuthResponse(
                success=False,
                message="User with this email already exists",
                error="USER_EXISTS"
            )

        # Check if phone number is already used
        existing_phone = session.exec(
            select(User).where(User.phone_number == request.phone_number)
        ).first()
        
        if existing_phone:
            return AuthResponse(
                success=False,
                message="Phone number is already registered",
                error="PHONE_EXISTS"
            )

        # Create new user
        hashed_password = auth_manager.hash_password(request.password)
        
        new_user = User(
            email=request.email,
            password_hash=hashed_password,
            first_name=request.first_name,
            last_name=request.last_name,
            phone_number=request.phone_number,
            role=UserRole.AGENT,
            is_active=True,
            is_verified=True,  # Verified via SMS
            email_verified_at=datetime.utcnow(),
            phone_verified_at=datetime.utcnow()
        )
        
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        # Create access token
        access_token = auth_manager.create_access_token(new_user)

        logger.info("User registered successfully", user_id=new_user.id, email=new_user.email)

        return AuthResponse(
            success=True,
            access_token=access_token,
            user_id=str(new_user.id),
            email=new_user.email,
            message="Registration successful"
        )

    except Exception as e:
        logger.error("User registration failed", error=str(e))
        raise HTTPException(status_code=500, detail="Registration failed")


@secure_auth_router.post("/login", response_model=AuthResponse)
async def login_user(
    request: LoginRequest,
    auth_manager: AuthManager = Depends(get_auth_manager),
    sms_service: SMSVerificationService = Depends(get_sms_verification_service),
    session: Session = Depends(get_session)
):
    """
    Secure login with email/password and SMS verification.
    
    Requires valid credentials and SMS verification code.
    """
    try:
        # Find user by email
        user = session.exec(
            select(User).where(User.email == request.email)
        ).first()

        if not user:
            return AuthResponse(
                success=False,
                message="Invalid email or password",
                error="INVALID_CREDENTIALS"
            )

        # Verify password
        if not auth_manager.verify_password(request.password, user.password_hash):
            return AuthResponse(
                success=False,
                message="Invalid email or password",
                error="INVALID_CREDENTIALS"
            )

        if not user.is_active:
            return AuthResponse(
                success=False,
                message="Account is deactivated",
                error="ACCOUNT_DEACTIVATED"
            )

        # Verify SMS code
        verification_success, verification_message = await sms_service.verify_code(
            request.phone_number, 
            request.sms_code, 
            session, 
            purpose="login"
        )
        
        if not verification_success:
            return AuthResponse(
                success=False,
                message=verification_message,
                error="SMS_VERIFICATION_FAILED"
            )

        # Verify phone number matches user
        if user.phone_number != request.phone_number:
            return AuthResponse(
                success=False,
                message="Phone number does not match account",
                error="PHONE_MISMATCH"
            )

        # Create access token
        access_token = auth_manager.create_access_token(user)

        # Update last login
        user.last_login = datetime.utcnow()
        session.commit()

        logger.info("User logged in successfully", user_id=user.id, email=user.email)

        return AuthResponse(
            success=True,
            access_token=access_token,
            user_id=str(user.id),
            email=user.email,
            message="Login successful"
        )

    except Exception as e:
        logger.error("User login failed", error=str(e))
        raise HTTPException(status_code=500, detail="Login failed")


@secure_auth_router.post("/check-user-exists")
async def check_user_exists(
    request: dict,
    session: Session = Depends(get_session)
):
    """
    Check if user exists by email or phone number.
    
    Used by frontend to determine if user should register or login.
    """
    try:
        email = request.get("email")
        phone_number = request.get("phone_number")
        
        user_exists = False
        user_data = None
        
        if email:
            user = session.exec(
                select(User).where(User.email == email)
            ).first()
            if user:
                user_exists = True
                user_data = {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone_number": user.phone_number
                }
        
        elif phone_number:
            user = session.exec(
                select(User).where(User.phone_number == phone_number)
            ).first()
            if user:
                user_exists = True
                user_data = {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone_number": user.phone_number
                }
        
        return {
            "exists": user_exists,
            "user": user_data,
            "action": "login" if user_exists else "register"
        }
        
    except Exception as e:
        logger.error("Failed to check user existence", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to check user")


@secure_auth_router.get("/verification-status/{phone_number}")
async def get_verification_status(
    phone_number: str,
    purpose: str = "login",
    session: Session = Depends(get_session)
):
    """
    Get SMS verification status for phone number.
    
    Returns information about pending verifications.
    """
    try:
        # Get latest verification
        verification = session.exec(
            select(SMSVerification).where(
                SMSVerification.phone_number == phone_number,
                SMSVerification.purpose == purpose,
                SMSVerification.is_expired == False
            ).order_by(SMSVerification.created_at.desc())
        ).first()
        
        if not verification:
            return {
                "has_pending": False,
                "message": "No pending verification found"
            }
        
        # Check if expired
        if verification.expires_at < datetime.utcnow():
            verification.is_expired = True
            session.commit()
            return {
                "has_pending": False,
                "message": "Verification code expired"
            }
        
        return {
            "has_pending": True,
            "verified": verification.is_verified,
            "attempts": verification.attempts,
            "max_attempts": 3,
            "expires_at": verification.expires_at.isoformat(),
            "message": "Verification code pending"
        }
        
    except Exception as e:
        logger.error("Failed to get verification status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get verification status")