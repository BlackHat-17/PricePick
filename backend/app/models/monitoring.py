"""
Monitoring models for price alerts and tracking
"""

from sqlalchemy import Column, Float, String, Boolean, ForeignKey, Text, Index, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
from .base import Base


class PriceAlert(Base):
    """
    Price alert model for user notifications
    """
    __tablename__ = "price_alerts"
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Alert configuration
    alert_type = Column(String(20), nullable=False, index=True)  # price_drop, price_increase, target_price
    target_price = Column(Float, nullable=True)  # For target_price alerts
    threshold_percentage = Column(Float, nullable=True)  # For percentage-based alerts
    threshold_amount = Column(Float, nullable=True)  # For amount-based alerts
    
    # Alert status
    is_active = Column(Boolean, default=True, nullable=False)
    is_triggered = Column(Boolean, default=False, nullable=False)
    triggered_at = Column(String(50), nullable=True)  # ISO datetime string
    last_checked = Column(String(50), nullable=True)  # ISO datetime string
    
    # Notification settings
    notify_email = Column(Boolean, default=True, nullable=False)
    notify_push = Column(Boolean, default=False, nullable=False)
    notify_sms = Column(Boolean, default=False, nullable=False)
    
    # Alert metadata
    notes = Column(Text, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="price_alerts")
    product = relationship("Product", back_populates="price_alerts")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_alert_user_active', 'user_id', 'is_active'),
        Index('idx_alert_product_active', 'product_id', 'is_active'),
        Index('idx_alert_type_active', 'alert_type', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<PriceAlert(id={self.id}, user_id={self.user_id}, product_id={self.product_id}, type='{self.alert_type}')>"
    
    def should_trigger(self, current_price: float) -> bool:
        """
        Check if alert should trigger based on current price
        """
        if not self.is_active or self.is_triggered:
            return False
        
        if self.alert_type == "price_drop":
            if self.threshold_percentage:
                # Check if price dropped by threshold percentage
                return current_price <= self.target_price * (1 - self.threshold_percentage / 100)
            elif self.threshold_amount:
                # Check if price dropped by threshold amount
                return current_price <= self.target_price - self.threshold_amount
            else:
                # Check if price is below target
                return current_price <= self.target_price
        
        elif self.alert_type == "price_increase":
            if self.threshold_percentage:
                # Check if price increased by threshold percentage
                return current_price >= self.target_price * (1 + self.threshold_percentage / 100)
            elif self.threshold_amount:
                # Check if price increased by threshold amount
                return current_price >= self.target_price + self.threshold_amount
            else:
                # Check if price is above target
                return current_price >= self.target_price
        
        elif self.alert_type == "target_price":
            # Check if price reached target
            return current_price <= self.target_price
        
        return False
    
    def trigger(self) -> None:
        """
        Mark alert as triggered
        """
        from datetime import datetime
        self.is_triggered = True
        self.triggered_at = datetime.utcnow().isoformat()
    
    def reset(self) -> None:
        """
        Reset alert for future triggering
        """
        self.is_triggered = False
        self.triggered_at = None


class PriceHistory(Base):
    """
    Price history model for storing detailed price tracking data
    """
    __tablename__ = "price_history"
    
    # Foreign key to product
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Price data
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Price context
    original_price = Column(Float, nullable=True)
    sale_price = Column(Float, nullable=True)
    shipping_cost = Column(Float, default=0.0, nullable=False)
    total_cost = Column(Float, nullable=True)
    
    # Price status
    is_sale = Column(Boolean, default=False, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    
    # Additional information
    seller = Column(String(200), nullable=True)
    condition = Column(String(50), nullable=True)
    source_url = Column(Text, nullable=True)
    
    # Tracking metadata
    scraping_session_id = Column(Integer, ForeignKey("scraping_sessions.id"), nullable=True)
    price_change_amount = Column(Float, nullable=True)
    price_change_percentage = Column(Float, nullable=True)
    
    # Additional data
    extra_metadata = Column("metadata", JSON, nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="price_history")
    scraping_session = relationship("ScrapingSession", back_populates="price_history")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_history_product_date', 'product_id', 'created_at'),
        Index('idx_history_currency', 'currency'),
        Index('idx_history_available', 'is_available', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<PriceHistory(id={self.id}, product_id={self.product_id}, price={self.price})>"
    
    @property
    def effective_price(self) -> float:
        """
        Get the effective price including shipping
        """
        return self.total_cost if self.total_cost else self.price + self.shipping_cost
    
    def calculate_price_change(self, previous_price: 'PriceHistory') -> None:
        """
        Calculate price change from previous price
        """
        if not previous_price or not previous_price.price:
            self.price_change_amount = 0.0
            self.price_change_percentage = 0.0
            return
        
        if previous_price.price == 0:
            self.price_change_amount = 0.0
            self.price_change_percentage = 0.0
            return
        
        self.price_change_amount = self.price - previous_price.price
        self.price_change_percentage = (self.price_change_amount / previous_price.price) * 100
