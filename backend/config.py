"""
Configuration management for PricePick backend
Centralized settings and environment variable handling
"""

import os
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # Application settings
    APP_NAME: str = "PricePick"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "pricepick"
    DATABASE_ECHO: bool = False
    # Optional SSL settings for MySQL
    DATABASE_SSL_CA: Optional[str] = None
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # CORS settings
    # Add your frontend URLs here (comma-separated or JSON array)
    # Default includes common development ports
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173",
    ]
    
    # Price monitoring settings
    PRICE_CHECK_INTERVAL: int = 3600  # 1 hour in seconds
    MAX_PRICE_HISTORY_DAYS: int = 90
    PRICE_CHANGE_THRESHOLD: float = 0.05  # 5% change threshold
    
    # Web scraping settings
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5
    USER_AGENT: str = "PricePick/1.0 (Price Tracking Bot)"
    
    # Notification settings
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_API_KEY: Optional[str] = None
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    
    # Cache settings
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 300  # 5 minutes
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if value is None:
            return value
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return []
            # Allow JSON array or comma-separated string
            if s.startswith("[") and s.endswith("]"):
                import json
                try:
                    return json.loads(s)
                except Exception:
                    # Fallback to comma-split if JSON invalid
                    return [origin.strip() for origin in s.split(",") if origin.strip()]
            return [origin.strip() for origin in s.split(",") if origin.strip()]
        return value
    
    @property
    def DATABASE_URL(self) -> str:
        """Build database URL from individual components"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Pydantic v2 settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore',  # ignore unrelated env vars (e.g., FIREBASE_*)
    )


# Create global settings instance
settings = Settings()


# Database configuration
DATABASE_CONFIG = {
    "url": settings.DATABASE_URL,
    "echo": settings.DATABASE_ECHO,
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "ssl_ca": settings.DATABASE_SSL_CA,
}

# Scraping configuration
SCRAPING_CONFIG = {
    "timeout": settings.REQUEST_TIMEOUT,
    "max_retries": settings.MAX_RETRIES,
    "retry_delay": settings.RETRY_DELAY,
    "user_agent": settings.USER_AGENT,
    "headers": {
        "User-Agent": settings.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
}

# Supported e-commerce platforms
SUPPORTED_PLATFORMS = {
    "amazon": {
        "name": "Amazon",
        "base_url": "https://www.amazon.com",
        "price_selectors": [
            ".a-price-whole",
            ".a-offscreen",
            "#priceblock_dealprice",
            "#priceblock_ourprice"
        ],
        "title_selectors": [
            "#productTitle",
            "h1.a-size-large"
        ]
    },
    "ebay": {
        "name": "eBay",
        "base_url": "https://www.ebay.com",
        "price_selectors": [
            ".notranslate",
            "#prcIsum",
            ".u-flL.condText"
        ],
        "title_selectors": [
            "h1#x-title-label-lbl",
            ".x-title-label"
        ]
    },
    "walmart": {
        "name": "Walmart",
        "base_url": "https://www.walmart.com",
        "price_selectors": [
            "[data-automation-id='product-price']",
            ".price-current",
            ".price-group"
        ],
        "title_selectors": [
            "h1[data-automation-id='product-title']",
            ".prod-ProductTitle"
        ]
    }
}

# Notification templates
NOTIFICATION_TEMPLATES = {
    "price_drop": {
        "subject": "Price Drop Alert - {product_name}",
        "body": """
        Great news! The price for {product_name} has dropped!
        
        Current Price: ${current_price}
        Previous Price: ${previous_price}
        Savings: ${savings} (${percentage_change}%)
        
        View Product: {product_url}
        """
    },
    "price_increase": {
        "subject": "Price Increase Alert - {product_name}",
        "body": """
        The price for {product_name} has increased.
        
        Current Price: ${current_price}
        Previous Price: ${previous_price}
        Increase: ${increase} (${percentage_change}%)
        
        View Product: {product_url}
        """
    }
}
