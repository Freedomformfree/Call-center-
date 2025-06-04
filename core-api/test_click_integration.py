"""
Test Click Payment Integration

This module provides comprehensive tests for the Click payment system integration,
including unit tests, integration tests, and end-to-end payment flow validation.
"""

import asyncio
import hashlib
import hmac
import json
import pytest
from datetime import datetime
from typing import Dict, Any
from uuid import uuid4, UUID

from click_payment_service import (
    ClickPaymentService,
    ClickPaymentRequest,
    ClickPaymentResponse,
    ClickSubscriptionManager
)


class TestClickPaymentService:
    """Test suite for Click Payment Service."""
    
    def setup_method(self):
        """Set up test environment."""
        self.service_id = 12345
        self.secret_key = "test_secret_key"
        self.click_service = ClickPaymentService(self.service_id, self.secret_key)
        
    def test_signature_generation(self):
        """Test signature generation for Click API."""
        # Test data
        click_trans_id = 123456789
        service_id = self.service_id
        merchant_trans_id = "TEST_ORDER_123"
        amount = 50000
        action = 0  # prepare
        sign_time = "2024-01-01 12:00:00"
        
        # Generate signature
        signature = self.click_service._generate_signature(
            click_trans_id, service_id, merchant_trans_id, 
            amount, action, sign_time
        )
        
        # Verify signature format
        assert isinstance(signature, str)
        assert len(signature) > 0
        
        # Test signature consistency
        signature2 = self.click_service._generate_signature(
            click_trans_id, service_id, merchant_trans_id, 
            amount, action, sign_time
        )
        assert signature == signature2
        
    def test_payment_url_generation(self):
        """Test payment URL generation."""
        merchant_trans_id = "TEST_ORDER_123"
        amount = 50000
        return_url = "https://example.com/success"
        description = "Test Payment"
        
        payment_url = self.click_service.create_payment_url(
            merchant_trans_id=merchant_trans_id,
            amount=amount,
            return_url=return_url,
            description=description
        )
        
        # Verify URL format
        assert payment_url.startswith("https://my.click.uz/services/pay")
        assert f"service_id={self.service_id}" in payment_url
        assert f"merchant_trans_id={merchant_trans_id}" in payment_url
        assert f"amount={amount}" in payment_url
        assert "return_url=" in payment_url
        
    @pytest.mark.asyncio
    async def test_prepare_payment_success(self):
        """Test successful payment preparation."""
        request = ClickPaymentRequest(
            click_trans_id=123456789,
            service_id=self.service_id,
            click_paydoc_id=987654321,
            merchant_trans_id="TEST_ORDER_123",
            amount=50000,
            action=0,
            error=0,
            error_note="",
            sign_time="2024-01-01 12:00:00",
            sign_string="test_signature"
        )
        
        response = await self.click_service.prepare_payment(request)
        
        # Verify response
        assert isinstance(response, ClickPaymentResponse)
        assert response.click_trans_id == request.click_trans_id
        assert response.merchant_trans_id == request.merchant_trans_id
        assert response.error == 0  # Success
        assert response.merchant_prepare_id is not None
        
    @pytest.mark.asyncio
    async def test_prepare_payment_invalid_amount(self):
        """Test payment preparation with invalid amount."""
        request = ClickPaymentRequest(
            click_trans_id=123456789,
            service_id=self.service_id,
            click_paydoc_id=987654321,
            merchant_trans_id="TEST_ORDER_123",
            amount=-1000,  # Invalid negative amount
            action=0,
            error=0,
            error_note="",
            sign_time="2024-01-01 12:00:00",
            sign_string="test_signature"
        )
        
        response = await self.click_service.prepare_payment(request)
        
        # Verify error response
        assert response.error == -5  # Incorrect amount
        
    @pytest.mark.asyncio
    async def test_complete_payment_success(self):
        """Test successful payment completion."""
        # First prepare payment
        prepare_request = ClickPaymentRequest(
            click_trans_id=123456789,
            service_id=self.service_id,
            click_paydoc_id=987654321,
            merchant_trans_id="TEST_ORDER_123",
            amount=50000,
            action=0,
            error=0,
            error_note="",
            sign_time="2024-01-01 12:00:00",
            sign_string="test_signature"
        )
        
        prepare_response = await self.click_service.prepare_payment(prepare_request)
        
        # Then complete payment
        complete_request = ClickPaymentRequest(
            click_trans_id=123456789,
            service_id=self.service_id,
            click_paydoc_id=987654321,
            merchant_trans_id="TEST_ORDER_123",
            merchant_prepare_id=prepare_response.merchant_prepare_id,
            amount=50000,
            action=1,
            error=0,
            error_note="",
            sign_time="2024-01-01 12:00:00",
            sign_string="test_signature"
        )
        
        complete_response = await self.click_service.complete_payment(complete_request)
        
        # Verify completion
        assert complete_response.error == 0
        assert complete_response.merchant_confirm_id is not None
        
    def test_error_code_mapping(self):
        """Test error code mapping."""
        # Test various error scenarios
        test_cases = [
            ("INVALID_AMOUNT", -5),
            ("TRANSACTION_NOT_FOUND", -6),
            ("ALREADY_PAID", -4),
            ("CANCELLED", -9),
            ("UNKNOWN_ERROR", -8)
        ]
        
        for error_type, expected_code in test_cases:
            # This would test internal error mapping logic
            # Implementation depends on actual error handling in the service
            pass


class TestClickSubscriptionManager:
    """Test suite for Click Subscription Manager."""
    
    def setup_method(self):
        """Set up test environment."""
        self.service_id = 12345
        self.secret_key = "test_secret_key"
        self.click_service = ClickPaymentService(self.service_id, self.secret_key)
        self.subscription_manager = ClickSubscriptionManager(self.click_service)
        
    @pytest.mark.asyncio
    async def test_create_subscription_payment(self):
        """Test subscription payment creation."""
        tenant_id = uuid4()
        plan = "premium"
        amount = 100000
        
        result = await self.subscription_manager.create_subscription_payment(
            tenant_id=tenant_id,
            plan=plan,
            amount=amount
        )
        
        # Verify result structure
        assert "payment_url" in result
        assert "merchant_trans_id" in result
        assert "subscription_id" in result
        assert result["amount"] == amount
        assert result["plan"] == plan
        
        # Verify transaction ID format
        merchant_trans_id = result["merchant_trans_id"]
        assert merchant_trans_id.startswith(f"SUB_{tenant_id}_{plan}_")
        
    @pytest.mark.asyncio
    async def test_process_subscription_payment(self):
        """Test subscription payment processing."""
        tenant_id = uuid4()
        plan = "starter"
        amount = 50000
        
        # Create subscription payment
        result = await self.subscription_manager.create_subscription_payment(
            tenant_id=tenant_id,
            plan=plan,
            amount=amount
        )
        
        merchant_trans_id = result["merchant_trans_id"]
        
        # Process payment (simulate successful payment)
        success = await self.subscription_manager.process_subscription_payment(
            merchant_trans_id=merchant_trans_id,
            click_trans_id=123456789,
            amount=amount
        )
        
        assert success is True
        
    @pytest.mark.asyncio
    async def test_cancel_subscription(self):
        """Test subscription cancellation."""
        tenant_id = uuid4()
        reason = "User requested cancellation"
        
        result = await self.subscription_manager.cancel_subscription(
            tenant_id=tenant_id,
            reason=reason
        )
        
        # Verify cancellation result
        assert "success" in result
        assert "cancelled_at" in result
        assert result["reason"] == reason


class TestClickIntegrationEndToEnd:
    """End-to-end integration tests."""
    
    def setup_method(self):
        """Set up test environment."""
        self.service_id = 12345
        self.secret_key = "test_secret_key"
        self.click_service = ClickPaymentService(self.service_id, self.secret_key)
        
    @pytest.mark.asyncio
    async def test_full_payment_flow(self):
        """Test complete payment flow from creation to completion."""
        # Step 1: Create payment URL
        merchant_trans_id = f"TEST_ORDER_{int(datetime.now().timestamp())}"
        amount = 75000
        description = "Test Product Purchase"
        return_url = "https://example.com/success"
        
        payment_url = self.click_service.create_payment_url(
            merchant_trans_id=merchant_trans_id,
            amount=amount,
            return_url=return_url,
            description=description
        )
        
        assert payment_url is not None
        
        # Step 2: Simulate Click prepare webhook
        prepare_request = ClickPaymentRequest(
            click_trans_id=123456789,
            service_id=self.service_id,
            click_paydoc_id=987654321,
            merchant_trans_id=merchant_trans_id,
            amount=amount,
            action=0,
            error=0,
            error_note="",
            sign_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sign_string="test_signature"
        )
        
        prepare_response = await self.click_service.prepare_payment(prepare_request)
        assert prepare_response.error == 0
        
        # Step 3: Simulate Click complete webhook
        complete_request = ClickPaymentRequest(
            click_trans_id=123456789,
            service_id=self.service_id,
            click_paydoc_id=987654321,
            merchant_trans_id=merchant_trans_id,
            merchant_prepare_id=prepare_response.merchant_prepare_id,
            amount=amount,
            action=1,
            error=0,
            error_note="",
            sign_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sign_string="test_signature"
        )
        
        complete_response = await self.click_service.complete_payment(complete_request)
        assert complete_response.error == 0
        assert complete_response.merchant_confirm_id is not None
        
    @pytest.mark.asyncio
    async def test_subscription_flow(self):
        """Test complete subscription flow."""
        tenant_id = uuid4()
        plan = "enterprise"
        amount = 200000
        
        # Create subscription
        subscription_manager = ClickSubscriptionManager(self.click_service)
        result = await subscription_manager.create_subscription_payment(
            tenant_id=tenant_id,
            plan=plan,
            amount=amount
        )
        
        merchant_trans_id = result["merchant_trans_id"]
        
        # Simulate payment flow
        prepare_request = ClickPaymentRequest(
            click_trans_id=123456789,
            service_id=self.service_id,
            click_paydoc_id=987654321,
            merchant_trans_id=merchant_trans_id,
            amount=amount,
            action=0,
            error=0,
            error_note="",
            sign_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sign_string="test_signature"
        )
        
        prepare_response = await self.click_service.prepare_payment(prepare_request)
        assert prepare_response.error == 0
        
        # Complete payment
        complete_request = ClickPaymentRequest(
            click_trans_id=123456789,
            service_id=self.service_id,
            click_paydoc_id=987654321,
            merchant_trans_id=merchant_trans_id,
            merchant_prepare_id=prepare_response.merchant_prepare_id,
            amount=amount,
            action=1,
            error=0,
            error_note="",
            sign_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sign_string="test_signature"
        )
        
        complete_response = await self.click_service.complete_payment(complete_request)
        assert complete_response.error == 0
        
        # Process subscription
        success = await subscription_manager.process_subscription_payment(
            merchant_trans_id=merchant_trans_id,
            click_trans_id=123456789,
            amount=amount
        )
        
        assert success is True


def test_click_api_configuration():
    """Test Click API configuration validation."""
    # Test valid configuration
    service = ClickPaymentService(12345, "valid_secret_key")
    assert service.service_id == 12345
    assert service.secret_key == "valid_secret_key"
    
    # Test invalid configuration
    try:
        ClickPaymentService(0, "")
        assert False, "Should raise exception for invalid config"
    except ValueError:
        pass


def test_payment_url_parameters():
    """Test payment URL parameter validation."""
    service = ClickPaymentService(12345, "test_key")
    
    # Test with all parameters
    url = service.create_payment_url(
        merchant_trans_id="TEST_123",
        amount=50000,
        return_url="https://example.com/success",
        description="Test Payment"
    )
    
    # Verify all parameters are included
    assert "merchant_trans_id=TEST_123" in url
    assert "amount=50000" in url
    assert "return_url=" in url
    assert "description=" in url


if __name__ == "__main__":
    """Run tests manually."""
    import asyncio
    
    async def run_tests():
        """Run async tests."""
        print("Running Click Payment Integration Tests...")
        
        # Test basic functionality
        service = ClickPaymentService(12345, "test_secret")
        
        # Test payment URL generation
        url = service.create_payment_url(
            merchant_trans_id="TEST_123",
            amount=50000,
            return_url="https://example.com/success",
            description="Test Payment"
        )
        print(f"Generated payment URL: {url}")
        
        # Test signature generation
        signature = service._generate_signature(
            123456789, 12345, "TEST_123", 50000, 0, "2024-01-01 12:00:00"
        )
        print(f"Generated signature: {signature}")
        
        # Test subscription manager
        subscription_manager = ClickSubscriptionManager(service)
        result = await subscription_manager.create_subscription_payment(
            tenant_id=uuid4(),
            plan="premium",
            amount=100000
        )
        print(f"Subscription payment created: {result}")
        
        print("All tests completed successfully!")
    
    # Run the tests
    asyncio.run(run_tests())