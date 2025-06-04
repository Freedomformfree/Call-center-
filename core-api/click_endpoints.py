"""
Click Payment API Endpoints

This module provides FastAPI endpoints for handling Click payment system
integration, including prepare/complete webhooks and payment creation.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
import structlog

from click_payment_service import (
    ClickPaymentService, 
    ClickPaymentRequest, 
    ClickPaymentResponse,
    ClickSubscriptionManager
)
from config import get_api_keys

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/payments/click", tags=["Click Payments"])


def get_click_service() -> ClickPaymentService:
    """Get configured Click payment service."""
    api_keys = get_api_keys()
    
    service_id = api_keys.click_service_id
    secret_key = api_keys.click_secret_key
    
    if not service_id or not secret_key:
        raise HTTPException(
            status_code=500,
            detail="Click API not configured. Please set CLICK_SERVICE_ID and CLICK_SECRET_KEY environment variables."
        )
    
    return ClickPaymentService(int(service_id), secret_key)


@router.post("/prepare")
async def click_prepare_webhook(
    request: ClickPaymentRequest,
    click_service: ClickPaymentService = Depends(get_click_service)
) -> ClickPaymentResponse:
    """
    Handle Click prepare payment webhook.
    
    This endpoint is called by Click system to validate and prepare payment.
    """
    logger.info("Received Click prepare request", 
               click_trans_id=request.click_trans_id,
               merchant_trans_id=request.merchant_trans_id,
               amount=request.amount)
    
    try:
        response = await click_service.prepare_payment(request)
        
        logger.info("Click prepare response", 
                   click_trans_id=request.click_trans_id,
                   error=response.error,
                   merchant_prepare_id=response.merchant_prepare_id)
        
        return response
        
    except Exception as e:
        logger.error("Error processing Click prepare request", 
                    error=str(e),
                    click_trans_id=request.click_trans_id)
        
        return ClickPaymentResponse(
            click_trans_id=request.click_trans_id,
            merchant_trans_id=request.merchant_trans_id,
            error=-8,
            error_note="Error in request from click"
        )


@router.post("/complete")
async def click_complete_webhook(
    request: ClickPaymentRequest,
    click_service: ClickPaymentService = Depends(get_click_service)
) -> ClickPaymentResponse:
    """
    Handle Click complete payment webhook.
    
    This endpoint is called by Click system to finalize payment.
    """
    logger.info("Received Click complete request",
               click_trans_id=request.click_trans_id,
               merchant_trans_id=request.merchant_trans_id,
               merchant_prepare_id=request.merchant_prepare_id,
               error=request.error)
    
    try:
        response = await click_service.complete_payment(request)
        
        # If payment was successful, handle post-payment actions
        if response.error == 0:
            await handle_successful_payment(request.merchant_trans_id, request.amount)
        
        logger.info("Click complete response",
                   click_trans_id=request.click_trans_id,
                   error=response.error,
                   merchant_confirm_id=response.merchant_confirm_id)
        
        return response
        
    except Exception as e:
        logger.error("Error processing Click complete request",
                    error=str(e),
                    click_trans_id=request.click_trans_id)
        
        return ClickPaymentResponse(
            click_trans_id=request.click_trans_id,
            merchant_trans_id=request.merchant_trans_id,
            error=-8,
            error_note="Error in request from click"
        )


@router.post("/create-payment")
async def create_payment(
    payment_data: Dict[str, Any],
    click_service: ClickPaymentService = Depends(get_click_service)
) -> Dict[str, Any]:
    """
    Create a new payment URL for Click system.
    
    Args:
        payment_data: Payment information including amount, description, etc.
    
    Returns:
        Payment URL and transaction details
    """
    try:
        amount = payment_data.get("amount")
        description = payment_data.get("description", "VoiceConnect Payment")
        return_url = payment_data.get("return_url", "https://your-domain.com/payment/success")
        merchant_trans_id = payment_data.get("merchant_trans_id")
        
        if not amount:
            raise HTTPException(status_code=400, detail="Amount is required")
        
        if not merchant_trans_id:
            merchant_trans_id = f"ORDER_{int(datetime.now().timestamp())}"
        
        payment_url = click_service.create_payment_url(
            merchant_trans_id=merchant_trans_id,
            amount=amount,
            return_url=return_url,
            description=description
        )
        
        logger.info("Payment URL created",
                   merchant_trans_id=merchant_trans_id,
                   amount=amount)
        
        return {
            "success": True,
            "payment_url": payment_url,
            "merchant_trans_id": merchant_trans_id,
            "amount": amount,
            "currency": "UZS",
            "description": description
        }
        
    except Exception as e:
        logger.error("Error creating payment URL", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-subscription")
async def create_subscription_payment(
    subscription_data: Dict[str, Any],
    click_service: ClickPaymentService = Depends(get_click_service)
) -> Dict[str, Any]:
    """
    Create a subscription payment through Click.
    
    Args:
        subscription_data: Subscription information including tenant_id, plan, amount
    
    Returns:
        Subscription payment details
    """
    try:
        tenant_id = subscription_data.get("tenant_id")
        plan = subscription_data.get("plan")
        amount = subscription_data.get("amount")
        
        if not all([tenant_id, plan, amount]):
            raise HTTPException(
                status_code=400, 
                detail="tenant_id, plan, and amount are required"
            )
        
        subscription_manager = ClickSubscriptionManager(click_service)
        result = await subscription_manager.create_subscription_payment(
            tenant_id=UUID(tenant_id),
            plan=plan,
            amount=amount
        )
        
        logger.info("Subscription payment created",
                   tenant_id=tenant_id,
                   plan=plan,
                   amount=amount)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error("Error creating subscription payment", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payment-status/{merchant_trans_id}")
async def get_payment_status(merchant_trans_id: str) -> Dict[str, Any]:
    """
    Get payment status by merchant transaction ID.
    
    Args:
        merchant_trans_id: Merchant transaction identifier
    
    Returns:
        Payment status information
    """
    try:
        # TODO: Implement actual payment status lookup from database
        # This should check the payment status in your database
        
        logger.info("Payment status requested", merchant_trans_id=merchant_trans_id)
        
        # Mock response - replace with actual database lookup
        return {
            "merchant_trans_id": merchant_trans_id,
            "status": "pending",  # pending, completed, failed, cancelled
            "amount": 0,
            "currency": "UZS",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Error getting payment status", 
                    error=str(e),
                    merchant_trans_id=merchant_trans_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel-payment")
async def cancel_payment(
    cancel_data: Dict[str, Any],
    click_service: ClickPaymentService = Depends(get_click_service)
) -> Dict[str, Any]:
    """
    Cancel a payment (for refunds or cancellations).
    
    Args:
        cancel_data: Cancellation information
    
    Returns:
        Cancellation result
    """
    try:
        merchant_trans_id = cancel_data.get("merchant_trans_id")
        reason = cancel_data.get("reason", "User requested cancellation")
        
        if not merchant_trans_id:
            raise HTTPException(status_code=400, detail="merchant_trans_id is required")
        
        # TODO: Implement actual payment cancellation logic
        # This should:
        # 1. Update payment status in database
        # 2. Process refund if applicable
        # 3. Send notifications
        
        logger.info("Payment cancellation requested",
                   merchant_trans_id=merchant_trans_id,
                   reason=reason)
        
        return {
            "success": True,
            "merchant_trans_id": merchant_trans_id,
            "status": "cancelled",
            "reason": reason,
            "cancelled_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Error cancelling payment",
                    error=str(e),
                    merchant_trans_id=cancel_data.get("merchant_trans_id"))
        raise HTTPException(status_code=500, detail=str(e))


async def handle_successful_payment(merchant_trans_id: str, amount: float) -> None:
    """
    Handle post-payment success actions.
    
    Args:
        merchant_trans_id: Merchant transaction ID
        amount: Payment amount
    """
    try:
        logger.info("Processing successful payment",
                   merchant_trans_id=merchant_trans_id,
                   amount=amount)
        
        # Determine payment type from transaction ID
        if merchant_trans_id.startswith("SUB_"):
            # Subscription payment
            await handle_subscription_success(merchant_trans_id)
        elif merchant_trans_id.startswith("ORDER_"):
            # One-time order payment
            await handle_order_success(merchant_trans_id)
        else:
            logger.warning("Unknown payment type", merchant_trans_id=merchant_trans_id)
        
    except Exception as e:
        logger.error("Error handling successful payment",
                    error=str(e),
                    merchant_trans_id=merchant_trans_id)


async def handle_subscription_success(merchant_trans_id: str) -> None:
    """Handle successful subscription payment."""
    try:
        # Parse subscription info from transaction ID
        parts = merchant_trans_id.split("_")
        if len(parts) >= 3:
            tenant_id = UUID(parts[1])
            plan = parts[2]
            
            # TODO: Implement subscription activation
            # 1. Update tenant subscription status
            # 2. Set subscription expiry date
            # 3. Enable plan features
            # 4. Send confirmation email
            
            logger.info("Subscription activated",
                       tenant_id=tenant_id,
                       plan=plan,
                       merchant_trans_id=merchant_trans_id)
        
    except Exception as e:
        logger.error("Error activating subscription",
                    error=str(e),
                    merchant_trans_id=merchant_trans_id)


async def handle_order_success(merchant_trans_id: str) -> None:
    """Handle successful order payment."""
    try:
        # TODO: Implement order fulfillment
        # 1. Update order status
        # 2. Process order items
        # 3. Send confirmation email
        # 4. Generate invoice
        
        logger.info("Order processed successfully",
                   merchant_trans_id=merchant_trans_id)
        
    except Exception as e:
        logger.error("Error processing order",
                    error=str(e),
                    merchant_trans_id=merchant_trans_id)


# Health check endpoint
@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check for Click payment service."""
    return {
        "status": "healthy",
        "service": "click_payments",
        "timestamp": datetime.now().isoformat()
    }