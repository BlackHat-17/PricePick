"""
Price model for storing price history and tracking
"""

from sqlalchemy import Column, Float, String, Boolean, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from .base import Base


class Price(Base):
    """
    Price model representing individual price records
    """
    __tablename__ = "prices"
    
    # Foreign key to product
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Price information
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Price context
    original_price = Column(Float, nullable=True)  # Original price when tracking started
    sale_price = Column(Float, nullable=True)  # Sale price if different from regular price
    shipping_cost = Column(Float, default=0.0, nullable=False)
    total_cost = Column(Float, nullable=True)  # Price + shipping
    
    # Price status
    is_sale = Column(Boolean, default=False, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    
    # Additional information
    seller = Column(String(200), nullable=True)
    condition = Column(String(50), nullable=True)  # new, used, refurbished, etc.
    notes = Column(Text, nullable=True)
    
    # Source information
    source_url = Column(Text, nullable=True)
    scraping_session_id = Column(Integer, ForeignKey("scraping_sessions.id"), nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="prices")
    scraping_session = relationship("ScrapingSession", back_populates="prices")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_price_product_date', 'product_id', 'created_at'),
        Index('idx_price_currency', 'currency'),
        Index('idx_price_available', 'is_available', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<Price(id={self.id}, product_id={self.product_id}, price={self.price})>"
    
    @property
    def effective_price(self) -> float:
        """
        Get the effective price including shipping
        """
        return self.total_cost if self.total_cost else self.price + self.shipping_cost
    
    @property
    def savings_amount(self) -> float:
        """
        Calculate savings amount from original price
        """
        if not self.original_price or not self.price:
            return 0.0
        return max(0, self.original_price - self.effective_price)
    
    @property
    def savings_percentage(self) -> float:
        """
        Calculate savings percentage from original price
        """
        if not self.original_price or not self.price:
            return 0.0
        
        if self.original_price == 0:
            return 0.0
            
        return (self.savings_amount / self.original_price) * 100
    
    def is_significant_change(self, previous_price: 'Price', threshold: float = 0.05) -> bool:
        """
        Check if this price represents a significant change from previous price
        """
        if not previous_price or not previous_price.price:
            return True
        
        if previous_price.price == 0:
            return True
            
        change_percentage = abs(self.price - previous_price.price) / previous_price.price
        return change_percentage >= threshold
