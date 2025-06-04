"""
Database Models Module

This module defines comprehensive database models for Project GeminiVoiceConnect,
implementing sophisticated business entities, relationships, and data structures
for multi-tenant SaaS operations, revenue optimization, and AI-driven automation.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column, JSON, Text
from sqlalchemy import Index, UniqueConstraint, CheckConstraint
from pydantic import validator, EmailStr, BaseModel
import structlog


logger = structlog.get_logger(__name__)


# Enums for type safety and validation
class UserRole(str, Enum):
    """User role enumeration."""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"


class TenantStatus(str, Enum):
    """Tenant status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class CallStatus(str, Enum):
    """Call status enumeration."""
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    CANCELLED = "cancelled"


class CallDirection(str, Enum):
    """Call direction enumeration."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CampaignStatus(str, Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LeadStatus(str, Enum):
    """Lead status enumeration."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"
    LOST = "lost"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class IntegrationType(str, Enum):
    """Integration type enumeration."""
    CRM = "crm"
    ECOMMERCE = "ecommerce"
    PAYMENT = "payment"
    COMMUNICATION = "communication"
    ANALYTICS = "analytics"
    CUSTOM = "custom"


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIAL = "trial"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ModemStatus(str, Enum):
    """Modem status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ASSIGNED = "assigned"
    AVAILABLE = "available"


class PhoneNumberType(str, Enum):
    """Phone number type enumeration."""
    COMPANY = "company"
    CLIENT = "client"
    TEMPORARY = "temporary"


class SMSStatus(str, Enum):
    """SMS status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


# Base Models
class TimestampMixin(SQLModel):
    """Mixin for timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class UUIDMixin(SQLModel):
    """Mixin for UUID primary key."""
    id: UUID = Field(default_factory=uuid4, primary_key=True)


# Core Business Models
class Tenant(UUIDMixin, TimestampMixin, table=True):
    """
    Tenant model for multi-tenant SaaS architecture.
    
    Represents individual customer organizations with complete
    isolation and resource management.
    """
    __tablename__ = "tenants"
    
    # Basic Information
    name: str = Field(max_length=255, nullable=False)
    slug: str = Field(max_length=100, nullable=False, unique=True)
    domain: Optional[str] = Field(max_length=255, default=None)
    
    # Contact Information
    email: EmailStr = Field(nullable=False)
    phone: Optional[str] = Field(max_length=20, default=None)
    address: Optional[str] = Field(max_length=500, default=None)
    
    # Status and Configuration
    status: TenantStatus = Field(default=TenantStatus.TRIAL, nullable=False)
    subscription_plan: str = Field(max_length=50, default="starter", nullable=False)
    trial_ends_at: Optional[datetime] = Field(default=None)
    
    # Resource Limits
    max_concurrent_calls: int = Field(default=10, nullable=False)
    max_daily_calls: int = Field(default=1000, nullable=False)
    max_sms_per_day: int = Field(default=1000, nullable=False)
    max_users: int = Field(default=5, nullable=False)
    max_modems: int = Field(default=5, nullable=False)
    
    # Business Configuration
    industry: Optional[str] = Field(max_length=100, default=None)
    company_size: Optional[str] = Field(max_length=50, default=None)
    timezone: str = Field(default="UTC", max_length=50, nullable=False)
    currency: str = Field(default="USD", max_length=3, nullable=False)
    
    # AI Configuration
    gemini_api_key: Optional[str] = Field(default=None)
    custom_prompts: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    ai_settings: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Feature Flags
    features_enabled: Dict[str, bool] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Billing Information
    billing_email: Optional[EmailStr] = Field(default=None)
    payment_method_id: Optional[str] = Field(max_length=255, default=None)
    
    # Relationships
    users: List["User"] = Relationship(back_populates="tenant")
    campaigns: List["Campaign"] = Relationship(back_populates="tenant")
    calls: List["Call"] = Relationship(back_populates="tenant")
    leads: List["Lead"] = Relationship(back_populates="tenant")
    integrations: List["Integration"] = Relationship(back_populates="tenant")
    
    __table_args__ = (
        Index("idx_tenant_slug", "slug"),
        Index("idx_tenant_status", "status"),
        Index("idx_tenant_domain", "domain"),
    )


class User(UUIDMixin, TimestampMixin, table=True):
    """
    User model for authentication and authorization.
    
    Represents individual users within tenant organizations
    with role-based access control and comprehensive profiles.
    """
    __tablename__ = "users"
    
    # Basic Information
    email: EmailStr = Field(nullable=False, unique=True)
    username: str = Field(max_length=100, nullable=False, unique=True)
    first_name: str = Field(max_length=100, nullable=False)
    last_name: str = Field(max_length=100, nullable=False)
    
    # Authentication
    password_hash: str = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    is_verified: bool = Field(default=False, nullable=False)
    last_login: Optional[datetime] = Field(default=None)
    
    # Authorization
    role: UserRole = Field(default=UserRole.AGENT, nullable=False)
    permissions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Profile Information
    phone: Optional[str] = Field(max_length=20, default=None)
    avatar_url: Optional[str] = Field(max_length=500, default=None)
    timezone: str = Field(default="UTC", max_length=50, nullable=False)
    language: str = Field(default="en", max_length=10, nullable=False)
    
    # Tenant Association
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False)
    tenant: Tenant = Relationship(back_populates="users")
    
    # Performance Metrics
    total_calls_handled: int = Field(default=0, nullable=False)
    average_call_duration: Optional[float] = Field(default=None)
    customer_satisfaction_score: Optional[float] = Field(default=None)
    
    # Settings
    notification_preferences: Dict[str, bool] = Field(default_factory=dict, sa_column=Column(JSON))
    ui_preferences: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_tenant", "tenant_id"),
        Index("idx_user_role", "role"),
        Index("idx_user_active", "is_active"),
    )


class Campaign(UUIDMixin, TimestampMixin, table=True):
    """
    Campaign model for automated calling campaigns.
    
    Represents intelligent calling campaigns with AI-driven
    optimization, scheduling, and performance tracking.
    """
    __tablename__ = "campaigns"
    
    # Basic Information
    name: str = Field(max_length=255, nullable=False)
    description: Optional[str] = Field(sa_column=Column(Text))
    
    # Campaign Configuration
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT, nullable=False)
    campaign_type: str = Field(max_length=50, nullable=False)  # sales, support, survey, etc.
    
    # Scheduling
    start_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    schedule_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # AI Configuration
    ai_prompt: str = Field(sa_column=Column(Text))
    conversation_goals: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    success_criteria: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Targeting
    target_audience: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    lead_filters: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Performance Metrics
    total_calls_made: int = Field(default=0, nullable=False)
    successful_calls: int = Field(default=0, nullable=False)
    leads_generated: int = Field(default=0, nullable=False)
    conversion_rate: float = Field(default=0.0, nullable=False)
    average_call_duration: float = Field(default=0.0, nullable=False)
    
    # Budget and Limits
    max_calls_per_day: Optional[int] = Field(default=None)
    max_total_calls: Optional[int] = Field(default=None)
    budget_limit: Optional[Decimal] = Field(max_digits=10, decimal_places=2, default=None)
    cost_per_call: Optional[Decimal] = Field(max_digits=6, decimal_places=4, default=None)
    
    # Tenant Association
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False)
    tenant: Tenant = Relationship(back_populates="campaigns")
    
    # Relationships
    calls: List["Call"] = Relationship(back_populates="campaign")
    leads: List["Lead"] = Relationship(back_populates="campaign")
    
    __table_args__ = (
        Index("idx_campaign_tenant", "tenant_id"),
        Index("idx_campaign_status", "status"),
        Index("idx_campaign_type", "campaign_type"),
        Index("idx_campaign_dates", "start_date", "end_date"),
    )


class Call(UUIDMixin, TimestampMixin, table=True):
    """
    Call model for comprehensive call tracking and analytics.
    
    Represents individual call sessions with detailed metadata,
    conversation analysis, and business intelligence data.
    """
    __tablename__ = "calls"
    
    # Basic Call Information
    phone_number: str = Field(max_length=20, nullable=False)
    direction: CallDirection = Field(nullable=False)
    status: CallStatus = Field(default=CallStatus.INITIATED, nullable=False)
    
    # Timing Information
    initiated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    answered_at: Optional[datetime] = Field(default=None)
    ended_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[int] = Field(default=None)
    
    # Technical Details
    modem_id: Optional[str] = Field(max_length=10, default=None)
    call_sid: Optional[str] = Field(max_length=100, default=None)
    audio_url: Optional[str] = Field(max_length=500, default=None)
    
    # Conversation Analysis
    transcript: Optional[str] = Field(sa_column=Column(Text))
    sentiment_score: Optional[float] = Field(default=None)
    conversation_summary: Optional[str] = Field(sa_column=Column(Text))
    key_topics: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Business Intelligence
    lead_qualified: bool = Field(default=False, nullable=False)
    appointment_scheduled: bool = Field(default=False, nullable=False)
    sale_made: bool = Field(default=False, nullable=False)
    sale_amount: Optional[Decimal] = Field(max_digits=10, decimal_places=2, default=None)
    
    # Customer Information
    customer_name: Optional[str] = Field(max_length=255, default=None)
    customer_email: Optional[EmailStr] = Field(default=None)
    customer_company: Optional[str] = Field(max_length=255, default=None)
    
    # AI Analysis
    ai_insights: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    action_items: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    follow_up_required: bool = Field(default=False, nullable=False)
    follow_up_date: Optional[datetime] = Field(default=None)
    
    # Quality Metrics
    audio_quality_score: Optional[float] = Field(default=None)
    conversation_quality_score: Optional[float] = Field(default=None)
    customer_satisfaction_score: Optional[float] = Field(default=None)
    
    # Associations
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False)
    tenant: Tenant = Relationship(back_populates="calls")
    
    campaign_id: Optional[UUID] = Field(foreign_key="campaigns.id", default=None)
    campaign: Optional[Campaign] = Relationship(back_populates="calls")
    
    lead_id: Optional[UUID] = Field(foreign_key="leads.id", default=None)
    lead: Optional["Lead"] = Relationship(back_populates="calls")
    
    __table_args__ = (
        Index("idx_call_tenant", "tenant_id"),
        Index("idx_call_phone", "phone_number"),
        Index("idx_call_status", "status"),
        Index("idx_call_direction", "direction"),
        Index("idx_call_campaign", "campaign_id"),
        Index("idx_call_initiated", "initiated_at"),
        Index("idx_call_modem", "modem_id"),
    )


class Lead(UUIDMixin, TimestampMixin, table=True):
    """
    Lead model for comprehensive lead management and tracking.
    
    Represents potential customers with detailed profiles,
    interaction history, and AI-driven scoring and insights.
    """
    __tablename__ = "leads"
    
    # Basic Information
    first_name: str = Field(max_length=100, nullable=False)
    last_name: str = Field(max_length=100, nullable=False)
    email: Optional[EmailStr] = Field(default=None)
    phone: str = Field(max_length=20, nullable=False)
    
    # Company Information
    company: Optional[str] = Field(max_length=255, default=None)
    job_title: Optional[str] = Field(max_length=100, default=None)
    industry: Optional[str] = Field(max_length=100, default=None)
    company_size: Optional[str] = Field(max_length=50, default=None)
    
    # Lead Management
    status: LeadStatus = Field(default=LeadStatus.NEW, nullable=False)
    source: str = Field(max_length=100, nullable=False)  # campaign, website, referral, etc.
    priority: int = Field(default=3, nullable=False)  # 1-5 scale
    
    # AI Scoring
    lead_score: float = Field(default=0.0, nullable=False)
    conversion_probability: Optional[float] = Field(default=None)
    lifetime_value_prediction: Optional[Decimal] = Field(max_digits=10, decimal_places=2, default=None)
    
    # Interaction History
    last_contacted: Optional[datetime] = Field(default=None)
    contact_attempts: int = Field(default=0, nullable=False)
    total_interactions: int = Field(default=0, nullable=False)
    
    # Preferences and Notes
    preferred_contact_time: Optional[str] = Field(max_length=100, default=None)
    timezone: Optional[str] = Field(max_length=50, default=None)
    language: str = Field(default="en", max_length=10, nullable=False)
    notes: Optional[str] = Field(sa_column=Column(Text))
    
    # Custom Fields
    custom_fields: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Associations
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False)
    tenant: Tenant = Relationship(back_populates="leads")
    
    campaign_id: Optional[UUID] = Field(foreign_key="campaigns.id", default=None)
    campaign: Optional[Campaign] = Relationship(back_populates="leads")
    
    # Relationships
    calls: List[Call] = Relationship(back_populates="lead")
    
    __table_args__ = (
        Index("idx_lead_tenant", "tenant_id"),
        Index("idx_lead_phone", "phone"),
        Index("idx_lead_email", "email"),
        Index("idx_lead_status", "status"),
        Index("idx_lead_score", "lead_score"),
        Index("idx_lead_campaign", "campaign_id"),
        Index("idx_lead_company", "company"),
    )


class Integration(UUIDMixin, TimestampMixin, table=True):
    """
    Integration model for external service connections.
    
    Represents connections to CRM systems, e-commerce platforms,
    payment processors, and other business applications.
    """
    __tablename__ = "integrations"
    
    # Basic Information
    name: str = Field(max_length=255, nullable=False)
    integration_type: IntegrationType = Field(nullable=False)
    provider: str = Field(max_length=100, nullable=False)  # salesforce, hubspot, shopify, etc.
    
    # Configuration
    is_active: bool = Field(default=True, nullable=False)
    config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    credentials: Dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Sync Information
    last_sync: Optional[datetime] = Field(default=None)
    sync_frequency: str = Field(default="hourly", max_length=20, nullable=False)
    auto_sync_enabled: bool = Field(default=True, nullable=False)
    
    # Status and Metrics
    status: str = Field(default="connected", max_length=20, nullable=False)
    total_synced_records: int = Field(default=0, nullable=False)
    last_error: Optional[str] = Field(sa_column=Column(Text))
    
    # Tenant Association
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False)
    tenant: Tenant = Relationship(back_populates="integrations")
    
    __table_args__ = (
        Index("idx_integration_tenant", "tenant_id"),
        Index("idx_integration_type", "integration_type"),
        Index("idx_integration_provider", "provider"),
        Index("idx_integration_active", "is_active"),
        UniqueConstraint("tenant_id", "provider", name="uq_tenant_provider"),
    )


class Payment(UUIDMixin, TimestampMixin, table=True):
    """
    Payment model for billing and transaction tracking.
    
    Represents payment transactions, subscriptions, and
    billing history for comprehensive financial management.
    """
    __tablename__ = "payments"
    
    # Basic Information
    amount: Decimal = Field(max_digits=10, decimal_places=2, nullable=False)
    currency: str = Field(default="USD", max_length=3, nullable=False)
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, nullable=False)
    
    # Payment Details
    payment_method: str = Field(max_length=50, nullable=False)  # card, bank_transfer, etc.
    payment_processor: str = Field(max_length=50, nullable=False)  # click, paypal, etc.
    transaction_id: str = Field(max_length=255, nullable=False, unique=True)
    
    # Billing Information
    billing_period_start: Optional[date] = Field(default=None)
    billing_period_end: Optional[date] = Field(default=None)
    invoice_number: Optional[str] = Field(max_length=100, default=None)
    
    # Processing Information
    processed_at: Optional[datetime] = Field(default=None)
    failure_reason: Optional[str] = Field(max_length=500, default=None)
    
    # Payment Metadata
    payment_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Tenant Association
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False)
    
    __table_args__ = (
        Index("idx_payment_tenant", "tenant_id"),
        Index("idx_payment_status", "status"),
        Index("idx_payment_transaction", "transaction_id"),
        Index("idx_payment_processor", "payment_processor"),
        Index("idx_payment_date", "processed_at"),
    )


class AuditLog(UUIDMixin, TimestampMixin, table=True):
    """
    Audit log model for compliance and security tracking.
    
    Represents all system activities for comprehensive
    audit trails and compliance reporting.
    """
    __tablename__ = "audit_logs"
    
    # Event Information
    event_type: str = Field(max_length=100, nullable=False)
    event_description: str = Field(max_length=500, nullable=False)
    
    # Actor Information
    user_id: Optional[UUID] = Field(foreign_key="users.id", default=None)
    user_email: Optional[str] = Field(max_length=255, default=None)
    ip_address: Optional[str] = Field(max_length=45, default=None)
    user_agent: Optional[str] = Field(max_length=500, default=None)
    
    # Resource Information
    resource_type: Optional[str] = Field(max_length=100, default=None)
    resource_id: Optional[str] = Field(max_length=255, default=None)
    
    # Change Information
    old_values: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON))
    new_values: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON))
    
    # Context
    tenant_id: Optional[UUID] = Field(foreign_key="tenants.id", default=None)
    session_id: Optional[str] = Field(max_length=255, default=None)
    
    # Audit Metadata
    audit_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    __table_args__ = (
        Index("idx_audit_tenant", "tenant_id"),
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_event", "event_type"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_timestamp", "created_at"),
    )


# Analytics and Reporting Models
class AnalyticsSnapshot(UUIDMixin, TimestampMixin, table=True):
    """
    Analytics snapshot model for time-series business intelligence.
    
    Stores aggregated metrics and KPIs for historical analysis
    and trend identification.
    """
    __tablename__ = "analytics_snapshots"
    
    # Time Information
    snapshot_date: date = Field(nullable=False)
    snapshot_hour: Optional[int] = Field(default=None)  # For hourly snapshots
    
    # Metrics
    total_calls: int = Field(default=0, nullable=False)
    successful_calls: int = Field(default=0, nullable=False)
    total_call_duration: int = Field(default=0, nullable=False)  # in seconds
    average_call_duration: float = Field(default=0.0, nullable=False)
    
    # Lead Metrics
    leads_generated: int = Field(default=0, nullable=False)
    leads_qualified: int = Field(default=0, nullable=False)
    conversion_rate: float = Field(default=0.0, nullable=False)
    
    # Revenue Metrics
    revenue_generated: Decimal = Field(default=0, max_digits=10, decimal_places=2, nullable=False)
    average_deal_size: Decimal = Field(default=0, max_digits=10, decimal_places=2, nullable=False)
    
    # Quality Metrics
    average_sentiment_score: Optional[float] = Field(default=None)
    customer_satisfaction_score: Optional[float] = Field(default=None)
    
    # Custom Metrics
    custom_metrics: Dict[str, float] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Tenant Association
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False)
    
    __table_args__ = (
        Index("idx_analytics_tenant", "tenant_id"),
        Index("idx_analytics_date", "snapshot_date"),
        Index("idx_analytics_tenant_date", "tenant_id", "snapshot_date"),
        UniqueConstraint("tenant_id", "snapshot_date", "snapshot_hour", name="uq_tenant_snapshot"),
    )


# New Models for Enhanced Functionality

class ClientRegistration(UUIDMixin, TimestampMixin, table=True):
    """
    Client registration model for new user registration process.
    
    Handles the complete registration workflow including SMS verification.
    """
    __tablename__ = "client_registrations"
    
    # Basic Information
    email: EmailStr = Field(nullable=False, unique=True)
    password_hash: str = Field(nullable=False)
    phone_number: str = Field(max_length=20, nullable=False)
    
    # Verification
    is_phone_verified: bool = Field(default=False, nullable=False)
    sms_code: Optional[str] = Field(max_length=6, default=None)
    sms_code_expires_at: Optional[datetime] = Field(default=None)
    verification_attempts: int = Field(default=0, nullable=False)
    
    # Registration Status
    is_completed: bool = Field(default=False, nullable=False)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    user_id: Optional[UUID] = Field(foreign_key="users.id", default=None)
    
    __table_args__ = (
        Index("idx_client_reg_email", "email"),
        Index("idx_client_reg_phone", "phone_number"),
        Index("idx_client_reg_status", "is_completed"),
    )


class Subscription(UUIDMixin, TimestampMixin, table=True):
    """
    Subscription model for managing client subscriptions.
    
    Handles monthly subscriptions and feature access control.
    """
    __tablename__ = "subscriptions"
    
    # Basic Information
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    plan_name: str = Field(max_length=100, nullable=False)
    status: SubscriptionStatus = Field(default=SubscriptionStatus.TRIAL, nullable=False)
    
    # Billing
    monthly_price: Decimal = Field(max_digits=8, decimal_places=2, nullable=False)
    currency: str = Field(default="USD", max_length=3, nullable=False)
    
    # Subscription Period
    start_date: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    end_date: datetime = Field(nullable=False)
    trial_end_date: Optional[datetime] = Field(default=None)
    
    # Features
    enabled_features: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    feature_limits: Dict[str, int] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Payment
    last_payment_date: Optional[datetime] = Field(default=None)
    next_payment_date: Optional[datetime] = Field(default=None)
    payment_method_id: Optional[str] = Field(max_length=255, default=None)
    
    # Auto-renewal
    auto_renew: bool = Field(default=True, nullable=False)
    cancelled_at: Optional[datetime] = Field(default=None)
    cancellation_reason: Optional[str] = Field(max_length=500, default=None)
    
    # Relationships
    user: "User" = Relationship()
    
    __table_args__ = (
        Index("idx_subscription_user", "user_id"),
        Index("idx_subscription_status", "status"),
        Index("idx_subscription_dates", "start_date", "end_date"),
    )


class Modem(UUIDMixin, TimestampMixin, table=True):
    """
    Modem model for managing physical modems and phone numbers.
    
    Represents individual modems with their phone numbers and status.
    """
    __tablename__ = "modems"
    
    # Basic Information
    modem_id: str = Field(max_length=20, nullable=False, unique=True)
    phone_number: str = Field(max_length=20, nullable=False, unique=True)
    phone_number_type: PhoneNumberType = Field(nullable=False)
    
    # Status
    status: ModemStatus = Field(default=ModemStatus.AVAILABLE, nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    
    # Assignment
    assigned_user_id: Optional[UUID] = Field(foreign_key="users.id", default=None)
    assigned_at: Optional[datetime] = Field(default=None)
    assignment_expires_at: Optional[datetime] = Field(default=None)
    
    # AI Configuration
    gemini_api_key: Optional[str] = Field(default=None)
    ai_prompt: Optional[str] = Field(sa_column=Column(Text))
    conversation_context: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Technical Details
    device_info: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    last_heartbeat: Optional[datetime] = Field(default=None)
    signal_strength: Optional[int] = Field(default=None)
    
    # Usage Statistics
    total_calls_handled: int = Field(default=0, nullable=False)
    total_sms_sent: int = Field(default=0, nullable=False)
    uptime_percentage: float = Field(default=0.0, nullable=False)
    
    # Relationships
    assigned_user: Optional["User"] = Relationship()
    
    __table_args__ = (
        Index("idx_modem_id", "modem_id"),
        Index("idx_modem_phone", "phone_number"),
        Index("idx_modem_status", "status"),
        Index("idx_modem_type", "phone_number_type"),
        Index("idx_modem_assigned", "assigned_user_id"),
    )


class TemporaryPhoneAssignment(UUIDMixin, TimestampMixin, table=True):
    """
    Temporary phone assignment model for 30-minute company number assignments.
    
    Manages temporary assignments of company phone numbers to clients.
    """
    __tablename__ = "temporary_phone_assignments"
    
    # Assignment Details
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    modem_id: UUID = Field(foreign_key="modems.id", nullable=False)
    phone_number: str = Field(max_length=20, nullable=False)
    
    # Timing
    assigned_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    expires_at: datetime = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    
    # Conversation Context
    conversation_summary: Optional[str] = Field(sa_column=Column(Text))
    client_needs: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    recommended_features: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Outcome
    subscription_offered: bool = Field(default=False, nullable=False)
    subscription_accepted: bool = Field(default=False, nullable=False)
    call_ended_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    user: "User" = Relationship()
    modem: Modem = Relationship()
    
    __table_args__ = (
        Index("idx_temp_assignment_user", "user_id"),
        Index("idx_temp_assignment_modem", "modem_id"),
        Index("idx_temp_assignment_active", "is_active"),
        Index("idx_temp_assignment_expires", "expires_at"),
    )


class SMSMessage(UUIDMixin, TimestampMixin, table=True):
    """
    SMS message model for tracking all SMS communications.
    
    Handles verification codes and other SMS communications.
    """
    __tablename__ = "sms_messages"
    
    # Basic Information
    phone_number: str = Field(max_length=20, nullable=False)
    message_content: str = Field(max_length=1000, nullable=False)
    message_type: str = Field(max_length=50, nullable=False)  # verification, notification, etc.
    
    # Status
    status: SMSStatus = Field(default=SMSStatus.PENDING, nullable=False)
    sent_at: Optional[datetime] = Field(default=None)
    delivered_at: Optional[datetime] = Field(default=None)
    failed_at: Optional[datetime] = Field(default=None)
    
    # Technical Details
    modem_id: Optional[str] = Field(max_length=20, default=None)
    external_id: Optional[str] = Field(max_length=100, default=None)
    error_message: Optional[str] = Field(max_length=500, default=None)
    
    # Associations
    user_id: Optional[UUID] = Field(foreign_key="users.id", default=None)
    registration_id: Optional[UUID] = Field(foreign_key="client_registrations.id", default=None)
    
    # Relationships
    user: Optional["User"] = Relationship()
    
    __table_args__ = (
        Index("idx_sms_phone", "phone_number"),
        Index("idx_sms_status", "status"),
        Index("idx_sms_type", "message_type"),
        Index("idx_sms_user", "user_id"),
        Index("idx_sms_sent", "sent_at"),
    )


class ConversationContext(UUIDMixin, TimestampMixin, table=True):
    """
    Conversation context model for storing daily conversation history.
    
    Stores conversation context for AI to maintain continuity.
    """
    __tablename__ = "conversation_contexts"
    
    # Basic Information
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    phone_number: str = Field(max_length=20, nullable=False)
    conversation_date: date = Field(nullable=False)
    
    # Context Data
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    key_topics: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    client_preferences: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    business_context: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # AI Insights
    sentiment_analysis: Dict[str, float] = Field(default_factory=dict, sa_column=Column(JSON))
    intent_analysis: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    action_items: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Metadata
    total_interactions: int = Field(default=0, nullable=False)
    last_interaction_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    # Relationships
    user: "User" = Relationship()
    
    __table_args__ = (
        Index("idx_conversation_user", "user_id"),
        Index("idx_conversation_phone", "phone_number"),
        Index("idx_conversation_date", "conversation_date"),
        UniqueConstraint("user_id", "phone_number", "conversation_date", name="uq_user_phone_date"),
    )


class AIToolConfig(UUIDMixin, TimestampMixin, table=True):
    """
    AI tool configuration model for storing user API integrations.
    
    Stores API keys and configurations for external services.
    """
    __tablename__ = "ai_tool_configs"
    
    # Basic Information
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    tool_name: str = Field(max_length=50, nullable=False)  # gmail, calendar, slack, etc.
    
    # Configuration
    config: Dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))  # API keys, tokens, etc.
    is_active: bool = Field(default=True, nullable=False)
    
    # Metadata
    last_used_at: Optional[datetime] = None
    usage_count: int = Field(default=0, nullable=False)
    
    # Relationships
    user: "User" = Relationship()
    
    __table_args__ = (
        Index("idx_ai_tool_user", "user_id"),
        Index("idx_ai_tool_name", "tool_name"),
        UniqueConstraint("user_id", "tool_name", name="uq_user_tool"),
    )


class AdminSettings(UUIDMixin, TimestampMixin, table=True):
    """
    Admin settings model for system configuration.
    
    Stores global system settings and configurations.
    """
    __tablename__ = "admin_settings"
    
    # Setting Information
    setting_key: str = Field(max_length=100, nullable=False, unique=True)
    setting_value: str = Field(sa_column=Column(Text))
    setting_type: str = Field(max_length=50, nullable=False)  # string, integer, boolean, json
    
    # Metadata
    description: Optional[str] = Field(max_length=500, default=None)
    category: str = Field(max_length=50, nullable=False)
    is_sensitive: bool = Field(default=False, nullable=False)
    
    # Versioning
    version: int = Field(default=1, nullable=False)
    previous_value: Optional[str] = Field(sa_column=Column(Text))
    changed_by: Optional[UUID] = Field(foreign_key="users.id", default=None)
    changed_at: Optional[datetime] = Field(default=None)
    
    __table_args__ = (
        Index("idx_admin_settings_key", "setting_key"),
        Index("idx_admin_settings_category", "category"),
    )


# Response Models
class TenantResponse(BaseModel):
    """Response model for tenant data"""
    id: UUID
    name: str
    domain: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CampaignResponse(BaseModel):
    """Response model for campaign data"""
    id: UUID
    name: str
    tenant_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LeadResponse(BaseModel):
    """Response model for lead data"""
    id: UUID
    name: str
    phone: str
    email: Optional[str] = None
    status: str
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime


class CallResponse(BaseModel):
    """Response model for call data"""
    id: UUID
    lead_id: UUID
    campaign_id: UUID
    status: str
    duration: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# Create Models
class TenantCreate(BaseModel):
    """Model for creating new tenants"""
    name: str
    domain: str
    is_active: bool = True


class CampaignCreate(BaseModel):
    """Model for creating new campaigns"""
    name: str
    tenant_id: UUID
    is_active: bool = True


class LeadCreate(BaseModel):
    """Model for creating new leads"""
    name: str
    phone: str
    email: Optional[str] = None
    status: str = "new"
    tenant_id: UUID


class CallCreate(BaseModel):
    """Model for creating new calls"""
    lead_id: UUID
    campaign_id: UUID
    status: str = "initiated"
    duration: Optional[int] = None


# Request Models
class AgenticFunctionRequest(BaseModel):
    """Request model for agentic functions"""
    function_name: str
    parameters: Dict[str, Any] = {}
    tenant_id: UUID


class RevenueOptimizationRequest(BaseModel):
    """Request model for revenue optimization"""
    tenant_id: UUID
    optimization_type: str
    parameters: Dict[str, Any] = {}


class AnalyticsRequest(BaseModel):
    """Request model for analytics"""
    tenant_id: UUID
    metric_type: str
    date_range: Dict[str, str]
    filters: Dict[str, Any] = {}


class ComplianceRequest(BaseModel):
    """Request model for compliance operations"""
    tenant_id: UUID
    operation_type: str
    data: Dict[str, Any] = {}


class NotificationRequest(BaseModel):
    """Request model for notifications"""
    tenant_id: UUID
    notification_type: str
    recipients: List[str]
    message: str
    channel: str = "email"


# Configuration Models
class IntegrationConfig(BaseModel):
    """Configuration model for integrations"""
    integration_type: str
    config_data: Dict[str, Any]
    is_enabled: bool = True


class SystemConfig(BaseModel):
    """System configuration model"""
    config_key: str
    config_value: Any
    config_type: str = "string"


class UserUpdate(BaseModel):
    """Model for updating user data"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class TenantUpdate(BaseModel):
    """Model for updating tenant data"""
    name: Optional[str] = None
    domain: Optional[str] = None
    is_active: Optional[bool] = None


class CampaignUpdate(BaseModel):
    """Model for updating campaign data"""
    name: Optional[str] = None
    is_active: Optional[bool] = None


class LeadUpdate(BaseModel):
    """Model for updating lead data"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[str] = None


# Validation and Business Logic
@validator('phone', pre=True, always=True)
def validate_phone_number(cls, v):
    """Validate phone number format."""
    if v and not v.startswith('+'):
        # Add basic validation logic
        pass
    return v


@validator('email', pre=True, always=True)
def validate_email_format(cls, v):
    """Validate email format."""
    if v and '@' not in v:
        raise ValueError('Invalid email format')
    return v