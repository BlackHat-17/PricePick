"""
Product model for storing product information
"""

from sqlalchemy import Column, String, Text, Float, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
from .base import Base


class Product(Base):
    """
    Product model representing items to track
    """
    __tablename__ = "products"
    
    # Basic product information
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    brand = Column(String(100), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    
    # Product identifiers
    sku = Column(String(100), nullable=True, unique=True, index=True)
    upc = Column(String(20), nullable=True, unique=True, index=True)
    asin = Column(String(20), nullable=True, unique=True, index=True)  # Amazon ASIN
    
    # E-commerce platform information
    platform = Column(String(50), nullable=False, index=True)  # amazon, ebay, walmart, etc.
    platform_product_id = Column(String(100), nullable=True, index=True)
    product_url = Column(Text, nullable=False)
    
    # Current pricing information
    current_price = Column(Float, nullable=True)
    original_price = Column(Float, nullable=True)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Product status
    is_available = Column(Boolean, default=True, nullable=False)
    is_tracking = Column(Boolean, default=True, nullable=False)
    
    # Additional metadata
    image_url = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, default=0, nullable=False)
    
    # Scraping configuration
    price_selector = Column(String(200), nullable=True)
    title_selector = Column(String(200), nullable=True)
    availability_selector = Column(String(200), nullable=True)
    
    # Custom fields for platform-specific data (avoid reserved attribute name)
    extra_metadata = Column("metadata", JSON, nullable=True)
    
    # Relationships
    prices = relationship("Price", back_populates="product", cascade="all, delete-orphan")
    price_alerts = relationship("PriceAlert", back_populates="product", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    scraping_sessions = relationship("ScrapingSession", back_populates="product", cascade="all, delete-orphan")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_product_platform_url', 'platform', 'product_url'),
        Index('idx_product_tracking', 'is_tracking', 'is_active'),
        Index('idx_product_category_brand', 'category', 'brand'),
    )
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', platform='{self.platform}')>"
    
    @property
    def latest_price(self) -> float:
        """
        Get the most recent price for this product
        """
        if self.prices:
            latest_price = max(self.prices, key=lambda p: p.created_at)
            return latest_price.price
        return self.current_price or 0.0
    
    @property
    def price_change_percentage(self) -> float:
        """
        Calculate price change percentage from original price
        """
        if not self.original_price or not self.current_price:
            return 0.0
        
        if self.original_price == 0:
            return 0.0
            
        return ((self.current_price - self.original_price) / self.original_price) * 100
    
    @property
    def is_on_sale(self) -> bool:
        """
        Check if product is currently on sale
        """
        if not self.original_price or not self.current_price:
            return False
        return self.current_price < self.original_price
    
    def get_price_trend(self, days: int = 30) -> str:
        """
        Get price trend over specified days
        Returns: 'increasing', 'decreasing', 'stable'
        """
        if not self.prices or len(self.prices) < 2:
            return 'stable'
        
        # Get prices from last N days
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_prices = [p for p in self.prices if p.created_at >= cutoff_date]
        
        if len(recent_prices) < 2:
            return 'stable'
        
        # Sort by date
        recent_prices.sort(key=lambda p: p.created_at)
        
        # Calculate trend
        first_price = recent_prices[0].price
        last_price = recent_prices[-1].price
        
        if last_price > first_price * 1.05:  # 5% increase
            return 'increasing'
        elif last_price < first_price * 0.95:  # 5% decrease
            return 'decreasing'
        else:
            return 'stable'
