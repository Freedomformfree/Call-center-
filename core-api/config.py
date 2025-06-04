"""
Core-API Configuration Module

This module provides comprehensive configuration management for the core-api
microservice, implementing type-safe configuration loading, validation, and
environment-specific settings for Project GeminiVoiceConnect.
"""

import os
from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import validator, Field


class CoreAPIConfig(BaseSettings):
    """
    Comprehensive configuration class for core-api microservice.
    
    Provides type-safe configuration management with validation,
    environment variable loading, and default values for all
    core-api operational parameters.
    """
    
    # Application Settings
    app_name: str = Field(default="GeminiVoiceConnect Core-API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="production", description="Environment (development/staging/production)")
    development_mode: bool = Field(default=True, description="Development mode for SMS simulation")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8001, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./ai_call_center.db", description="Database connection URL")
    db_pool_size: int = Field(default=20, description="Database connection pool size")
    db_max_overflow: int = Field(default=30, description="Database max overflow connections")
    db_echo: bool = Field(default=False, description="Database query logging")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    redis_pool_size: int = Field(default=50, description="Redis connection pool size")
    redis_timeout: int = Field(default=5, description="Redis connection timeout")
    
    # Security Configuration
    secret_key: str = Field(default="demo-secret-key-change-in-production", description="Application secret key")
    jwt_secret_key: str = Field(default="demo-jwt-secret-key-change-in-production", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT token expiration hours")
    password_hash_rounds: int = Field(default=12, description="Password hashing rounds")
    encryption_key: str = Field(default="8yylVG_tHWHkdhc328ng3HcDewGDnXcF8IynbdWqRzk=", description="Encryption key for sensitive data")
    
    # API Configuration
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    cors_methods: List[str] = Field(default=["*"], description="CORS allowed methods")
    cors_headers: List[str] = Field(default=["*"], description="CORS allowed headers")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=1000, description="API rate limit per minute")
    rate_limit_per_hour: int = Field(default=10000, description="API rate limit per hour")
    
    # External Services
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    voice_bridge_url: str = Field(default="http://voice-bridge:8000", description="Voice-bridge service URL")
    
    # Payment Processing
    stripe_api_key: Optional[str] = Field(default=None, description="Stripe API key")
    stripe_webhook_secret: Optional[str] = Field(default=None, description="Stripe webhook secret")
    paypal_client_id: Optional[str] = Field(default=None, description="PayPal client ID")
    paypal_client_secret: Optional[str] = Field(default=None, description="PayPal client secret")
    
    # Communication Services
    sendgrid_api_key: Optional[str] = Field(default=None, description="SendGrid API key")
    
    # Integration Services
    salesforce_client_id: Optional[str] = Field(default=None, description="Salesforce client ID")
    salesforce_client_secret: Optional[str] = Field(default=None, description="Salesforce client secret")
    hubspot_api_key: Optional[str] = Field(default=None, description="HubSpot API key")
    shopify_api_key: Optional[str] = Field(default=None, description="Shopify API key")
    
    # Monitoring & Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json/text)")
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    
    # Business Configuration
    default_tenant_limits: Dict[str, int] = Field(
        default={
            "max_concurrent_calls": 100,
            "max_daily_calls": 10000,
            "max_sms_per_day": 10000,
            "max_users": 50
        },
        description="Default tenant resource limits"
    )
    
    # Feature Flags
    healthcare_module_enabled: bool = Field(default=False, description="Enable healthcare module")
    legal_module_enabled: bool = Field(default=False, description="Enable legal module")
    real_estate_module_enabled: bool = Field(default=False, description="Enable real estate module")
    home_services_module_enabled: bool = Field(default=False, description="Enable home services module")
    ml_training_enabled: bool = Field(default=True, description="Enable ML model training")
    predictive_analytics_enabled: bool = Field(default=True, description="Enable predictive analytics")
    
    # Compliance Configuration
    gdpr_enabled: bool = Field(default=True, description="Enable GDPR compliance")
    hipaa_enabled: bool = Field(default=False, description="Enable HIPAA compliance")
    data_retention_days: int = Field(default=2555, description="Data retention period in days")
    audit_log_enabled: bool = Field(default=True, description="Enable audit logging")
    
    # Performance Configuration
    max_request_size: int = Field(default=16 * 1024 * 1024, description="Maximum request size in bytes")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    background_task_timeout: int = Field(default=300, description="Background task timeout in seconds")
    
    # Backup Configuration
    backup_enabled: bool = Field(default=True, description="Enable automated backups")
    backup_interval_hours: int = Field(default=24, description="Backup interval in hours")
    backup_retention_days: int = Field(default=30, description="Backup retention in days")
    
    @validator('database_url')
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://', 'sqlite:///')):
            raise ValueError('Database URL must be PostgreSQL or SQLite')
        return v
    
    @validator('redis_url')
    def validate_redis_url(cls, v):
        """Validate Redis URL format."""
        if not v.startswith('redis://'):
            raise ValueError('Redis URL must start with redis://')
        return v
    
    @validator('secret_key', 'jwt_secret_key')
    def validate_secret_keys(cls, v):
        """Validate secret key length."""
        if len(v) < 32:
            raise ValueError('Secret keys must be at least 32 characters long')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_environments = ['development', 'staging', 'production']
        if v not in valid_environments:
            raise ValueError(f'Environment must be one of: {valid_environments}')
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration dictionary."""
        return {
            "url": self.database_url,
            "pool_size": self.db_pool_size,
            "max_overflow": self.db_max_overflow,
            "echo": self.db_echo
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration dictionary."""
        return {
            "url": self.redis_url,
            "pool_size": self.redis_pool_size,
            "timeout": self.redis_timeout
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration dictionary."""
        return {
            "secret_key": self.secret_key,
            "jwt_secret_key": self.jwt_secret_key,
            "jwt_algorithm": self.jwt_algorithm,
            "jwt_expiration_hours": self.jwt_expiration_hours,
            "password_hash_rounds": self.password_hash_rounds
        }
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration dictionary."""
        return {
            "allow_origins": self.cors_origins,
            "allow_methods": self.cors_methods,
            "allow_headers": self.cors_headers,
            "allow_credentials": True
        }
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get all feature flags."""
        return {
            "healthcare_module": self.healthcare_module_enabled,
            "legal_module": self.legal_module_enabled,
            "real_estate_module": self.real_estate_module_enabled,
            "home_services_module": self.home_services_module_enabled,
            "ml_training": self.ml_training_enabled,
            "predictive_analytics": self.predictive_analytics_enabled,
            "gdpr": self.gdpr_enabled,
            "hipaa": self.hipaa_enabled,
            "audit_log": self.audit_log_enabled
        }


# Global settings instance
_settings: Optional[CoreAPIConfig] = None


def get_settings() -> CoreAPIConfig:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = CoreAPIConfig()
    return _settings