"""
Click Payment Service Module

This module implements the Click API payment processing system for Uzbekistan,
replacing Stripe with local payment infrastructure. Supports both prepare and
complete payment flows as per Click API documentation.
"""

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

import structlog
from fastapi import HTTPException
from pydantic import BaseModel, Field, validator

logger = structlog.get_logger(__name__)


class ClickPaymentRequest(BaseModel):
    """Click payment request model for prepare/complete actions."""
    click_trans_id: int = Field(..., description="Transaction ID in CLICK system")
    service_id: int = Field(..., description="Service ID")
    click_paydoc_id: int = Field(..., description="Payment ID in CLICK system")
    merchant_trans_id: str = Field(..., description="Order ID in merchant system")
    amount: float = Field(..., description="Payment amount in soums")
    action: int = Field(..., description="Action: 0=Prepare, 1=Complete")
    error: int = Field(..., description="Error code: 0=success")
    error_note: str = Field(..., description="Error description")
    sign_time: str = Field(..., description="Payment date YYYY-MM-DD HH:mm:ss")
    sign_string: str = Field(..., description="MD5 hash for authentication")
    
    # Complete action specific fields
    merchant_prepare_id: Optional[int] = Field(None, description="Prepare ID from merchant")


class ClickPaymentResponse(BaseModel):
    """Click payment response model."""
    click_trans_id: int
    merchant_trans_id: str
    merchant_prepare_id: Optional[int] = None
    merchant_confirm_id: Optional[int] = None
    error: int
    error_note: str


class ClickPaymentService:
    """
    Click Payment Service for processing payments through Click API.
    
    Implements the two-stage payment process:
    1. Prepare - Validate and reserve payment
    2. Complete - Finalize payment transaction
    """
    
    def __init__(self, service_id: int, secret_key: str):
        """
        Initialize Click payment service.
        
        Args:
            service_id: Click service identifier
            secret_key: Secret key provided by Click
        """
        self.service_id = service_id
        self.secret_key = secret_key
        self.error_codes = {
            0: "Success",
            -1: "SIGN CHECK FAILED",
            -2: "Incorrect parameter amount",
            -3: "Action not found",
            -4: "Already paid",
            -5: "User does not exist",
            -6: "Transaction does not exist",
            -7: "Failed to update user",
            -8: "Error in request from click",
            -9: "Transaction cancelled"
        }
    
    def generate_sign_string(self, click_trans_id: int, merchant_trans_id: str, 
                           amount: float, action: int, sign_time: str,
                           merchant_prepare_id: Optional[int] = None) -> str:
        """
        Generate MD5 signature for Click API authentication.
        
        Args:
            click_trans_id: Click transaction ID
            merchant_trans_id: Merchant transaction ID
            amount: Payment amount
            action: Action type (0=prepare, 1=complete)
            sign_time: Signature timestamp
            merchant_prepare_id: Prepare ID (for complete action)
            
        Returns:
            MD5 hash string
        """
        if action == 0:  # Prepare
            sign_string = f"{click_trans_id}{self.service_id}{self.secret_key}{merchant_trans_id}{amount}{action}{sign_time}"
        else:  # Complete
            sign_string = f"{click_trans_id}{self.service_id}{self.secret_key}{merchant_trans_id}{merchant_prepare_id}{amount}{action}{sign_time}"
        
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()
    
    def verify_signature(self, request: ClickPaymentRequest) -> bool:
        """
        Verify the signature of incoming Click request.
        
        Args:
            request: Click payment request
            
        Returns:
            True if signature is valid
        """
        expected_sign = self.generate_sign_string(
            request.click_trans_id,
            request.merchant_trans_id,
            request.amount,
            request.action,
            request.sign_time,
            request.merchant_prepare_id
        )
        
        return expected_sign == request.sign_string
    
    async def prepare_payment(self, request: ClickPaymentRequest) -> ClickPaymentResponse:
        """
        Handle prepare payment request from Click.
        
        Validates the payment request and reserves the order/service.
        
        Args:
            request: Click payment request
            
        Returns:
            Click payment response
        """
        logger.info("Processing Click prepare payment", 
                   click_trans_id=request.click_trans_id,
                   merchant_trans_id=request.merchant_trans_id,
                   amount=request.amount)
        
        # Verify signature
        if not self.verify_signature(request):
            logger.error("Invalid signature for prepare payment",
                        click_trans_id=request.click_trans_id)
            return ClickPaymentResponse(
                click_trans_id=request.click_trans_id,
                merchant_trans_id=request.merchant_trans_id,
                error=-1,
                error_note="SIGN CHECK FAILED"
            )
        
        try:
            # Validate merchant transaction
            merchant_prepare_id = await self._validate_and_prepare_order(
                request.merchant_trans_id, 
                request.amount
            )
            
            if merchant_prepare_id is None:
                return ClickPaymentResponse(
                    click_trans_id=request.click_trans_id,
                    merchant_trans_id=request.merchant_trans_id,
                    error=-6,
                    error_note="Transaction does not exist"
                )
            
            logger.info("Payment prepared successfully",
                       click_trans_id=request.click_trans_id,
                       merchant_prepare_id=merchant_prepare_id)
            
            return ClickPaymentResponse(
                click_trans_id=request.click_trans_id,
                merchant_trans_id=request.merchant_trans_id,
                merchant_prepare_id=merchant_prepare_id,
                error=0,
                error_note="Success"
            )
            
        except Exception as e:
            logger.error("Error preparing payment", 
                        error=str(e),
                        click_trans_id=request.click_trans_id)
            return ClickPaymentResponse(
                click_trans_id=request.click_trans_id,
                merchant_trans_id=request.merchant_trans_id,
                error=-8,
                error_note="Error in request from click"
            )
    
    async def complete_payment(self, request: ClickPaymentRequest) -> ClickPaymentResponse:
        """
        Handle complete payment request from Click.
        
        Finalizes the payment and activates the service/order.
        
        Args:
            request: Click payment request
            
        Returns:
            Click payment response
        """
        logger.info("Processing Click complete payment",
                   click_trans_id=request.click_trans_id,
                   merchant_trans_id=request.merchant_trans_id,
                   merchant_prepare_id=request.merchant_prepare_id)
        
        # Verify signature
        if not self.verify_signature(request):
            logger.error("Invalid signature for complete payment",
                        click_trans_id=request.click_trans_id)
            return ClickPaymentResponse(
                click_trans_id=request.click_trans_id,
                merchant_trans_id=request.merchant_trans_id,
                error=-1,
                error_note="SIGN CHECK FAILED"
            )
        
        try:
            # Check if payment was successful (error = 0)
            if request.error != 0:
                # Payment failed, cancel the order
                await self._cancel_order(request.merchant_trans_id, request.merchant_prepare_id)
                return ClickPaymentResponse(
                    click_trans_id=request.click_trans_id,
                    merchant_trans_id=request.merchant_trans_id,
                    error=-9,
                    error_note="Transaction cancelled"
                )
            
            # Complete the payment
            merchant_confirm_id = await self._complete_order(
                request.merchant_trans_id,
                request.merchant_prepare_id,
                request.amount
            )
            
            if merchant_confirm_id is None:
                return ClickPaymentResponse(
                    click_trans_id=request.click_trans_id,
                    merchant_trans_id=request.merchant_trans_id,
                    error=-6,
                    error_note="Transaction does not exist"
                )
            
            logger.info("Payment completed successfully",
                       click_trans_id=request.click_trans_id,
                       merchant_confirm_id=merchant_confirm_id)
            
            return ClickPaymentResponse(
                click_trans_id=request.click_trans_id,
                merchant_trans_id=request.merchant_trans_id,
                merchant_confirm_id=merchant_confirm_id,
                error=0,
                error_note="Success"
            )
            
        except Exception as e:
            logger.error("Error completing payment",
                        error=str(e),
                        click_trans_id=request.click_trans_id)
            return ClickPaymentResponse(
                click_trans_id=request.click_trans_id,
                merchant_trans_id=request.merchant_trans_id,
                error=-8,
                error_note="Error in request from click"
            )
    
    async def _validate_and_prepare_order(self, merchant_trans_id: str, amount: float) -> Optional[int]:
        """
        Validate order and prepare for payment.
        
        Args:
            merchant_trans_id: Merchant transaction ID
            amount: Payment amount
            
        Returns:
            Merchant prepare ID if successful, None otherwise
        """
        # TODO: Implement actual order validation logic
        # This should check:
        # 1. Order exists and is valid
        # 2. Amount matches order total
        # 3. Order is not already paid
        # 4. Reserve the order/service
        
        # For now, return a mock prepare ID
        # In production, this should interact with your database
        logger.info("Validating order for preparation",
                   merchant_trans_id=merchant_trans_id,
                   amount=amount)
        
        # Mock validation - replace with actual logic
        if merchant_trans_id.startswith("SUB_"):
            # Subscription payment
            return int(str(uuid4().int)[:8])
        elif merchant_trans_id.startswith("ORDER_"):
            # One-time order payment
            return int(str(uuid4().int)[:8])
        else:
            return None
    
    async def _complete_order(self, merchant_trans_id: str, merchant_prepare_id: int, amount: float) -> Optional[int]:
        """
        Complete the order after successful payment.
        
        Args:
            merchant_trans_id: Merchant transaction ID
            merchant_prepare_id: Prepare ID from prepare stage
            amount: Payment amount
            
        Returns:
            Merchant confirm ID if successful, None otherwise
        """
        # TODO: Implement actual order completion logic
        # This should:
        # 1. Activate the subscription/service
        # 2. Send confirmation emails
        # 3. Update user account
        # 4. Generate invoice
        
        logger.info("Completing order after payment",
                   merchant_trans_id=merchant_trans_id,
                   merchant_prepare_id=merchant_prepare_id,
                   amount=amount)
        
        # Mock completion - replace with actual logic
        return int(str(uuid4().int)[:8])
    
    async def _cancel_order(self, merchant_trans_id: str, merchant_prepare_id: Optional[int]) -> None:
        """
        Cancel the order due to payment failure.
        
        Args:
            merchant_trans_id: Merchant transaction ID
            merchant_prepare_id: Prepare ID from prepare stage
        """
        # TODO: Implement actual order cancellation logic
        # This should:
        # 1. Remove order reservation
        # 2. Restore inventory if applicable
        # 3. Send cancellation notification
        
        logger.info("Cancelling order due to payment failure",
                   merchant_trans_id=merchant_trans_id,
                   merchant_prepare_id=merchant_prepare_id)
    
    def create_payment_url(self, merchant_trans_id: str, amount: float, 
                          return_url: str, description: str = "") -> str:
        """
        Create Click payment URL for redirecting users.
        
        Args:
            merchant_trans_id: Merchant transaction ID
            amount: Payment amount in soums
            return_url: URL to redirect after payment
            description: Payment description
            
        Returns:
            Click payment URL
        """
        # Click payment URL format
        base_url = "https://my.click.uz/services/pay"
        
        params = {
            "service_id": self.service_id,
            "merchant_id": merchant_trans_id,
            "amount": amount,
            "transaction_param": merchant_trans_id,
            "return_url": return_url,
            "description": description
        }
        
        # Build query string
        query_params = "&".join([f"{k}={v}" for k, v in params.items()])
        payment_url = f"{base_url}?{query_params}"
        
        logger.info("Generated Click payment URL",
                   merchant_trans_id=merchant_trans_id,
                   amount=amount)
        
        return payment_url


class ClickSubscriptionManager:
    """
    Manager for Click-based subscription payments.
    
    Handles subscription creation, renewal, and cancellation
    using Click payment infrastructure.
    """
    
    def __init__(self, click_service: ClickPaymentService):
        """
        Initialize subscription manager.
        
        Args:
            click_service: Click payment service instance
        """
        self.click_service = click_service
    
    async def create_subscription_payment(self, tenant_id: UUID, plan: str, 
                                        amount: float) -> Dict[str, Any]:
        """
        Create a subscription payment through Click.
        
        Args:
            tenant_id: Tenant UUID
            plan: Subscription plan name
            amount: Monthly amount in soums
            
        Returns:
            Payment details including Click URL
        """
        merchant_trans_id = f"SUB_{tenant_id}_{plan}_{int(datetime.now().timestamp())}"
        
        # Create payment URL
        return_url = f"https://your-domain.com/payment/success"
        description = f"VoiceConnect Pro - {plan} subscription"
        
        payment_url = self.click_service.create_payment_url(
            merchant_trans_id=merchant_trans_id,
            amount=amount,
            return_url=return_url,
            description=description
        )
        
        logger.info("Created subscription payment",
                   tenant_id=tenant_id,
                   plan=plan,
                   merchant_trans_id=merchant_trans_id)
        
        return {
            "payment_url": payment_url,
            "merchant_trans_id": merchant_trans_id,
            "amount": amount,
            "currency": "UZS",
            "description": description
        }
    
    async def handle_subscription_payment_success(self, merchant_trans_id: str) -> bool:
        """
        Handle successful subscription payment.
        
        Args:
            merchant_trans_id: Merchant transaction ID
            
        Returns:
            True if subscription was activated successfully
        """
        try:
            # Parse transaction ID to get tenant and plan info
            parts = merchant_trans_id.split("_")
            if len(parts) >= 3 and parts[0] == "SUB":
                tenant_id = UUID(parts[1])
                plan = parts[2]
                
                # TODO: Activate subscription in database
                # This should:
                # 1. Update tenant subscription status
                # 2. Set subscription expiry date
                # 3. Enable plan features
                # 4. Send confirmation email
                
                logger.info("Subscription activated successfully",
                           tenant_id=tenant_id,
                           plan=plan,
                           merchant_trans_id=merchant_trans_id)
                
                return True
            
        except Exception as e:
            logger.error("Failed to activate subscription",
                        error=str(e),
                        merchant_trans_id=merchant_trans_id)
        
        return False


# Error code mappings for Click API
CLICK_ERROR_CODES = {
    0: "Success",
    -1: "SIGN CHECK FAILED",
    -2: "Incorrect parameter amount", 
    -3: "Action not found",
    -4: "Already paid",
    -5: "User does not exist",
    -6: "Transaction does not exist",
    -7: "Failed to update user",
    -8: "Error in request from click",
    -9: "Transaction cancelled"
}