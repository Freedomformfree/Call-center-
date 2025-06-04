"""
API Keys Configuration
Central configuration for all API keys except Gemini (managed per-module in admin panel)
"""

import os
from typing import Optional

class APIKeysConfig:
    """Centralized API keys configuration"""
    
    def __init__(self):
        # SMS & Communication APIs (Local SIM800C modules)
        self.use_local_gsm: bool = os.getenv('USE_LOCAL_GSM', 'true').lower() == 'true'
        self.sim800c_port: Optional[str] = os.getenv('SIM800C_PORT', '/dev/ttyUSB0')
        self.sim800c_baudrate: int = int(os.getenv('SIM800C_BAUDRATE', '9600'))
        
        # Voice & Call APIs
        self.vonage_api_key: Optional[str] = os.getenv('VONAGE_API_KEY')
        self.vonage_api_secret: Optional[str] = os.getenv('VONAGE_API_SECRET')
        
        # Business Intelligence APIs
        self.openai_api_key: Optional[str] = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key: Optional[str] = os.getenv('ANTHROPIC_API_KEY')
        
        # CRM & Business APIs
        self.hubspot_api_key: Optional[str] = os.getenv('HUBSPOT_API_KEY')
        self.salesforce_client_id: Optional[str] = os.getenv('SALESFORCE_CLIENT_ID')
        self.salesforce_client_secret: Optional[str] = os.getenv('SALESFORCE_CLIENT_SECRET')
        
        # Payment Processing
        self.click_service_id: Optional[str] = os.getenv('CLICK_SERVICE_ID')
        self.click_secret_key: Optional[str] = os.getenv('CLICK_SECRET_KEY')
        self.click_merchant_id: Optional[str] = os.getenv('CLICK_MERCHANT_ID')
        self.paypal_client_id: Optional[str] = os.getenv('PAYPAL_CLIENT_ID')
        self.paypal_client_secret: Optional[str] = os.getenv('PAYPAL_CLIENT_SECRET')
        
        # Social Media & Marketing
        self.facebook_app_id: Optional[str] = os.getenv('FACEBOOK_APP_ID')
        self.facebook_app_secret: Optional[str] = os.getenv('FACEBOOK_APP_SECRET')
        self.google_client_id: Optional[str] = os.getenv('GOOGLE_CLIENT_ID')
        self.google_client_secret: Optional[str] = os.getenv('GOOGLE_CLIENT_SECRET')
        
        # Analytics & Tracking
        self.google_analytics_tracking_id: Optional[str] = os.getenv('GOOGLE_ANALYTICS_TRACKING_ID')
        self.mixpanel_token: Optional[str] = os.getenv('MIXPANEL_TOKEN')
        
        # Email Services
        self.sendgrid_api_key: Optional[str] = os.getenv('SENDGRID_API_KEY')
        self.mailgun_api_key: Optional[str] = os.getenv('MAILGUN_API_KEY')
        self.mailgun_domain: Optional[str] = os.getenv('MAILGUN_DOMAIN')
        
        # Cloud Storage
        self.aws_access_key_id: Optional[str] = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key: Optional[str] = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region: Optional[str] = os.getenv('AWS_REGION', 'us-east-1')
        
        # Database & Cache
        self.redis_url: Optional[str] = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.mongodb_url: Optional[str] = os.getenv('MONGODB_URL')
        
        # Security & Authentication
        self.jwt_secret_key: str = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
        self.encryption_key: Optional[str] = os.getenv('ENCRYPTION_KEY')
        
        # Telegram Bot
        self.telegram_bot_token: Optional[str] = os.getenv('TELEGRAM_BOT_TOKEN')
        
        # Business APIs
        self.yandex_taxi_api_key: Optional[str] = os.getenv('YANDEX_TAXI_API_KEY')
        self.apify_api_token: Optional[str] = os.getenv('APIFY_API_TOKEN')
        
        # Webhook URLs
        self.webhook_base_url: Optional[str] = os.getenv('WEBHOOK_BASE_URL')
        
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service"""
        return getattr(self, f"{service}_api_key", None)
    
    def is_service_configured(self, service: str) -> bool:
        """Check if a service is properly configured"""
        key = self.get_api_key(service)
        return key is not None and key.strip() != ""
    
    def get_configured_services(self) -> list:
        """Get list of all configured services"""
        configured = []
        for attr_name in dir(self):
            if attr_name.endswith('_api_key') and not attr_name.startswith('_'):
                service = attr_name.replace('_api_key', '')
                if self.is_service_configured(service):
                    configured.append(service)
        return configured
    
    def validate_required_keys(self) -> dict:
        """Validate that required API keys are present"""
        required_keys = {
            'jwt_secret_key': self.jwt_secret_key,
            'redis_url': self.redis_url,
        }
        
        missing_keys = []
        for key, value in required_keys.items():
            if not value or value.strip() == "":
                missing_keys.append(key)
        
        return {
            'valid': len(missing_keys) == 0,
            'missing_keys': missing_keys
        }

# Global instance
api_keys = APIKeysConfig()