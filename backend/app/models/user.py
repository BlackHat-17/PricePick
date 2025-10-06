"""
User model for authentication and user management
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text

from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime, timedelta
from .base import Base


class User(Base):
    """
    User model for authentication and user preferences
    """
    __tablename__ = "users"
    
    # Basic user information
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # User profile
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    
    # Email preferences
    email_notifications = Column(Boolean, default=True, nullable=False)
    price_drop_alerts = Column(Boolean, default=True, nullable=False)
    weekly_summary = Column(Boolean, default=True, nullable=False)
    marketing_emails = Column(Boolean, default=False, nullable=False)
    
    # Notification settings
    notification_frequency = Column(String(20), default="immediate", nullable=False)  # immediate, daily, weekly
    price_change_threshold = Column(String(10), default="5%", nullable=False)  # 1%, 5%, 10%, 25%
    
    # User preferences
    preferred_currency = Column(String(3), default="USD", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    language = Column(String(5), default="en", nullable=False)
    
    # Account metadata
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # API access
    api_key = Column(String(100), unique=True, nullable=True, index=True)
    api_usage_count = Column(Integer, default=0, nullable=False)
    api_usage_limit = Column(Integer, default=1000, nullable=False)  # Requests per month
    
    # Additional user data
    preferences = Column(JSON, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)
    
    # Relationships
    price_alerts = relationship("PriceAlert", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    @property
    def full_name(self) -> str:
        """
        Get user's full name
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    @property
    def is_locked(self) -> bool:
        """
        Check if user account is locked
        """
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until
    
    def lock_account(self, duration_minutes: int = 30) -> None:
        """
        Lock user account for specified duration
        """
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.failed_login_attempts += 1
    
    def unlock_account(self) -> None:
        """
        Unlock user account
        """
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def can_use_api(self) -> bool:
        """
        Check if user can make API requests
        """
        if not self.is_active or self.is_locked:
            return False
        
        # Check API usage limits (simplified - in production, use proper rate limiting)
        return self.api_usage_count < self.api_usage_limit
    
    def increment_api_usage(self) -> None:
        """
        Increment API usage counter
        """
        self.api_usage_count += 1
    
    def reset_api_usage(self) -> None:
        """
        Reset API usage counter (typically called monthly)
        """
        self.api_usage_count = 0
