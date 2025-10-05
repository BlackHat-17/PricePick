"""
Pydantic schemas for price-related API models
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PriceResponse(BaseModel):
    """Schema for price response"""
    id: int
    product_id: int
    price: float
    currency: str
    original_price: Optional[float]
    sale_price: Optional[float]
    shipping_cost: float
    total_cost: Optional[float]
    is_sale: bool
    is_available: bool
    seller: Optional[str]
    condition: Optional[str]
    notes: Optional[str]
    source_url: Optional[str]
    created_at: datetime
    
    # Computed fields
    effective_price: Optional[float] = None
    savings_amount: Optional[float] = None
    savings_percentage: Optional[float] = None
    
    class Config:
        from_attributes = True


class PriceHistoryResponse(BaseModel):
    """Schema for price history response"""
    product_id: int
    prices: List[PriceResponse]
    stats: Dict[str, Any]
    days: int
    
    class Config:
        from_attributes = True


class PriceStatsResponse(BaseModel):
    """Schema for price statistics response"""
    product_id: int
    total_prices: int
    current_price: Optional[float]
    min_price: Optional[float]
    max_price: Optional[float]
    avg_price: Optional[float]
    price_trend: str
    price_change_percentage: float
    volatility: Optional[float] = None
    
    class Config:
        from_attributes = True


class PriceTrendResponse(BaseModel):
    """Schema for price trend response"""
    product_id: int
    product_name: str
    platform: str
    category: Optional[str]
    current_price: Optional[float]
    price_count: int
    avg_price: Optional[float]
    min_price: Optional[float]
    max_price: Optional[float]
    trend: str
    
    class Config:
        from_attributes = True


class PriceDropResponse(BaseModel):
    """Schema for price drop response"""
    product_id: int
    product_name: str
    platform: str
    current_price: float
    original_price: float
    savings_amount: float
    savings_percentage: float
    avg_price: Optional[float]
    
    class Config:
        from_attributes = True


class PriceIncreaseResponse(BaseModel):
    """Schema for price increase response"""
    product_id: int
    product_name: str
    platform: str
    current_price: float
    original_price: float
    increase_amount: float
    increase_percentage: float
    avg_price: Optional[float]
    
    class Config:
        from_attributes = True


class PriceComparisonResponse(BaseModel):
    """Schema for price comparison response"""
    product1: Dict[str, Any]
    product2: Dict[str, Any]
    comparison: Dict[str, Any]
    
    class Config:
        from_attributes = True
