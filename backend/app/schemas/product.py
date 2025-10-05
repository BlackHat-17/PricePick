"""
Pydantic schemas for product-related API models
"""

from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class PlatformEnum(str, Enum):
    """Supported e-commerce platforms"""
    AMAZON = "amazon"
    EBAY = "ebay"
    WALMART = "walmart"
    TARGET = "target"
    BESTBUY = "bestbuy"
    HOMEDEPOT = "homedepot"
    LOWES = "lowes"


class ProductCreate(BaseModel):
    """Schema for creating a new product"""
    name: str = Field(..., min_length=1, max_length=500, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    sku: Optional[str] = Field(None, max_length=100, description="Product SKU")
    upc: Optional[str] = Field(None, max_length=20, description="Product UPC")
    asin: Optional[str] = Field(None, max_length=20, description="Amazon ASIN")
    platform: PlatformEnum = Field(..., description="E-commerce platform")
    platform_product_id: Optional[str] = Field(None, max_length=100, description="Platform-specific product ID")
    product_url: HttpUrl = Field(..., description="Product URL")
    currency: str = Field("USD", max_length=3, description="Currency code")
    image_url: Optional[HttpUrl] = Field(None, description="Product image URL")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Product rating")
    review_count: Optional[int] = Field(0, ge=0, description="Number of reviews")
    price_selector: Optional[str] = Field(None, max_length=200, description="Custom CSS selector for price")
    title_selector: Optional[str] = Field(None, max_length=200, description="Custom CSS selector for title")
    availability_selector: Optional[str] = Field(None, max_length=200, description="Custom CSS selector for availability")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional product metadata")
    
    @validator('currency')
    def validate_currency(cls, v):
        if v and len(v) != 3:
            raise ValueError('Currency must be a 3-letter code')
        return v.upper() if v else v


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    brand: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    upc: Optional[str] = Field(None, max_length=20)
    asin: Optional[str] = Field(None, max_length=20)
    platform: Optional[PlatformEnum] = None
    platform_product_id: Optional[str] = Field(None, max_length=100)
    product_url: Optional[HttpUrl] = None
    currency: Optional[str] = Field(None, max_length=3)
    image_url: Optional[HttpUrl] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    review_count: Optional[int] = Field(None, ge=0)
    price_selector: Optional[str] = Field(None, max_length=200)
    title_selector: Optional[str] = Field(None, max_length=200)
    availability_selector: Optional[str] = Field(None, max_length=200)
    is_tracking: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('currency')
    def validate_currency(cls, v):
        if v and len(v) != 3:
            raise ValueError('Currency must be a 3-letter code')
        return v.upper() if v else v


class ProductResponse(BaseModel):
    """Schema for product response"""
    id: int
    name: str
    description: Optional[str]
    brand: Optional[str]
    category: Optional[str]
    sku: Optional[str]
    upc: Optional[str]
    asin: Optional[str]
    platform: str
    platform_product_id: Optional[str]
    product_url: str
    current_price: Optional[float]
    original_price: Optional[float]
    currency: str
    is_available: bool
    is_tracking: bool
    image_url: Optional[str]
    rating: Optional[float]
    review_count: int
    price_selector: Optional[str]
    title_selector: Optional[str]
    availability_selector: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    latest_price: Optional[float] = None
    price_change_percentage: Optional[float] = None
    is_on_sale: Optional[bool] = None
    price_trend: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema for paginated product list response"""
    products: List[ProductResponse]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


class ProductStatsResponse(BaseModel):
    """Schema for product statistics response"""
    product_id: int
    total_prices: int
    current_price: Optional[float]
    min_price: Optional[float]
    max_price: Optional[float]
    avg_price: Optional[float]
    price_trend: str
    is_on_sale: Optional[bool]
    price_change_percentage: Optional[float]
    
    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    """Schema for product search query"""
    query: str = Field(..., min_length=1, max_length=200, description="Search keywords")
    limit_per_platform: int = Field(5, ge=1, le=20, description="Max results per platform")
    platforms: Optional[List[PlatformEnum]] = Field(None, description="Platforms to search; default all")


class SearchResultItem(BaseModel):
    """Single search result item"""
    platform: str
    title: str
    price: Optional[float] = None
    currency: Optional[str] = None
    product_url: str
    image_url: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None


class SearchResponse(BaseModel):
    """Aggregated search response across platforms"""
    query: str
    results: List[SearchResultItem]