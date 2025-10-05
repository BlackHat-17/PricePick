"""
Pydantic schemas for monitoring and alert-related API models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AlertTypeEnum(str, Enum):
    """Price alert types"""
    PRICE_DROP = "price_drop"
    PRICE_INCREASE = "price_increase"
    TARGET_PRICE = "target_price"


class PriceAlertCreate(BaseModel):
    """Schema for creating a price alert"""
    product_id: int = Field(..., description="Product ID to monitor")
    alert_type: AlertTypeEnum = Field(..., description="Type of alert")
    target_price: Optional[float] = Field(None, gt=0, description="Target price for alert")
    threshold_percentage: Optional[float] = Field(None, ge=0.1, le=100, description="Percentage threshold")
    threshold_amount: Optional[float] = Field(None, gt=0, description="Amount threshold")
    notify_email: bool = Field(True, description="Send email notifications")
    notify_push: bool = Field(False, description="Send push notifications")
    notify_sms: bool = Field(False, description="Send SMS notifications")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('target_price', 'threshold_percentage', 'threshold_amount')
    def validate_alert_parameters(cls, v, values):
        alert_type = values.get('alert_type')
        
        if alert_type == 'target_price' and not v:
            raise ValueError('target_price is required for target_price alerts')
        
        if alert_type in ['price_drop', 'price_increase'] and not v:
            raise ValueError('threshold_percentage or threshold_amount is required for price change alerts')
        
        return v


class PriceAlertUpdate(BaseModel):
    """Schema for updating a price alert"""
    alert_type: Optional[AlertTypeEnum] = None
    target_price: Optional[float] = Field(None, gt=0)
    threshold_percentage: Optional[float] = Field(None, ge=0.1, le=100)
    threshold_amount: Optional[float] = Field(None, gt=0)
    notify_email: Optional[bool] = None
    notify_push: Optional[bool] = None
    notify_sms: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[Dict[str, Any]] = None


class PriceAlertResponse(BaseModel):
    """Schema for price alert response"""
    id: int
    user_id: int
    product_id: int
    alert_type: str
    target_price: Optional[float]
    threshold_percentage: Optional[float]
    threshold_amount: Optional[float]
    is_active: bool
    is_triggered: bool
    triggered_at: Optional[str]
    last_checked: Optional[str]
    notify_email: bool
    notify_push: bool
    notify_sms: bool
    notes: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MonitoringStatsResponse(BaseModel):
    """Schema for monitoring statistics response"""
    total_alerts: int
    active_alerts: int
    triggered_alerts: int
    tracked_products: int
    recent_price_changes: int
    alert_types: Dict[str, int]
    
    class Config:
        from_attributes = True


class PriceHistoryResponse(BaseModel):
    """Schema for price history response"""
    product_id: int
    prices: List[Dict[str, Any]]
    stats: Dict[str, Any]
    days: int
    
    class Config:
        from_attributes = True


class AlertCheckResponse(BaseModel):
    """Schema for alert check response"""
    checked_count: int
    triggered_count: int
    success: bool
    message: Optional[str] = None
    
    class Config:
        from_attributes = True


class PriceChangeTrendResponse(BaseModel):
    """Schema for price change trend response"""
    product_id: int
    product_name: str
    platform: str
    category: Optional[str]
    current_price: Optional[float]
    original_price: Optional[float]
    change_amount: float
    change_percentage: float
    price_count: int
    avg_price: Optional[float]
    trend: str
    
    class Config:
        from_attributes = True


class NotificationPreferences(BaseModel):
    """Schema for notification preferences"""
    email_notifications: bool = Field(True, description="Enable email notifications")
    price_drop_alerts: bool = Field(True, description="Enable price drop alerts")
    weekly_summary: bool = Field(True, description="Enable weekly summary emails")
    marketing_emails: bool = Field(False, description="Enable marketing emails")
    notification_frequency: str = Field("immediate", description="Notification frequency")
    price_change_threshold: str = Field("5%", description="Price change threshold")
    
    @validator('notification_frequency')
    def validate_frequency(cls, v):
        allowed_values = ['immediate', 'daily', 'weekly']
        if v not in allowed_values:
            raise ValueError(f'notification_frequency must be one of: {allowed_values}')
        return v
    
    @validator('price_change_threshold')
    def validate_threshold(cls, v):
        allowed_values = ['1%', '5%', '10%', '25%']
        if v not in allowed_values:
            raise ValueError(f'price_change_threshold must be one of: {allowed_values}')
        return v
