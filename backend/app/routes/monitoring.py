"""
Price monitoring and alerting API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.monitoring import PriceAlert, PriceHistory
from app.schemas.monitoring import (
    PriceAlertCreate, PriceAlertUpdate, PriceAlertResponse,
    PriceHistoryResponse, MonitoringStatsResponse
)
from app.services.monitoring_service import MonitoringService
from app.services.alert_service import AlertService
from app.services.auth_service import AuthService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/alerts", response_model=PriceAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_price_alert(
    alert_data: PriceAlertCreate,
    user_id: int = Query(..., description="Firebase-authenticated user id"),
    db: Session = Depends(get_db)
):
    """
    Create a new price alert
    """
    try:
        alert_service = AlertService(db)
        
        # Create alert for provided user_id (validated by Firebase at gateway)
        alert = await alert_service.create_alert(user_id, alert_data)
        
        logger.info(f"Created price alert: {alert.id} for user {current_user.id}")
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create price alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create price alert: {str(e)}"
        )


@router.get("/alerts", response_model=List[PriceAlertResponse])
async def list_price_alerts(
    user_id: int = Query(..., description="Firebase-authenticated user id"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    skip: int = Query(0, ge=0, description="Number of alerts to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of alerts to return"),
    db: Session = Depends(get_db)
):
    """
    List price alerts for current user
    """
    try:
        alert_service = AlertService(db)
        
        # Get alerts
        filters = {
            "is_active": is_active,
            "alert_type": alert_type,
            "product_id": product_id
        }
        
        alerts = await alert_service.list_user_alerts(
            user_id=user_id,
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        return alerts
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list price alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price alerts"
        )


@router.get("/alerts/{alert_id}", response_model=PriceAlertResponse)
async def get_price_alert(
    alert_id: int,
    user_id: int = Query(..., description="Firebase-authenticated user id"),
    db: Session = Depends(get_db)
):
    """
    Get a specific price alert
    """
    try:
        alert_service = AlertService(db)
        
        # Get alert
        alert = await alert_service.get_alert(alert_id)
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Price alert not found"
            )
        
        # Check if user owns the alert
        if alert.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get price alert {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price alert"
        )


@router.put("/alerts/{alert_id}", response_model=PriceAlertResponse)
async def update_price_alert(
    alert_id: int,
    alert_data: PriceAlertUpdate,
    user_id: int = Query(..., description="Firebase-authenticated user id"),
    db: Session = Depends(get_db)
):
    """
    Update a price alert
    """
    try:
        alert_service = AlertService(db)
        
        # Get alert
        alert = await alert_service.get_alert(alert_id)
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Price alert not found"
            )
        
        # Check if user owns the alert
        if alert.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update alert
        updated_alert = await alert_service.update_alert(alert_id, alert_data)
        
        logger.info(f"Updated price alert: {alert_id}")
        return updated_alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update price alert {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update price alert: {str(e)}"
        )


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_price_alert(
    alert_id: int,
    user_id: int = Query(..., description="Firebase-authenticated user id"),
    db: Session = Depends(get_db)
):
    """
    Delete a price alert
    """
    try:
        alert_service = AlertService(db)
        
        # Get alert
        alert = await alert_service.get_alert(alert_id)
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Price alert not found"
            )
        
        # Check if user owns the alert
        if alert.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Delete alert
        success = await alert_service.delete_alert(alert_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete price alert"
            )
        
        logger.info(f"Deleted price alert: {alert_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete price alert {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete price alert"
        )


@router.post("/alerts/{alert_id}/toggle", response_model=dict)
async def toggle_price_alert(
    alert_id: int,
    user_id: int = Query(..., description="Firebase-authenticated user id"),
    db: Session = Depends(get_db)
):
    """
    Toggle price alert active status
    """
    try:
        alert_service = AlertService(db)
        
        # Get alert
        alert = await alert_service.get_alert(alert_id)
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Price alert not found"
            )
        
        # Check if user owns the alert
        if alert.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Toggle alert
        new_status = not alert.is_active
        await alert_service.toggle_alert(alert_id, new_status)
        
        logger.info(f"Toggled price alert {alert_id}: {new_status}")
        return {
            "alert_id": alert_id,
            "is_active": new_status,
            "message": f"Alert {'activated' if new_status else 'deactivated'}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle price alert {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle price alert"
        )


@router.get("/history/{product_id}", response_model=PriceHistoryResponse)
async def get_price_history(
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve prices for"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of prices to return"),
    db: Session = Depends(get_db)
):
    """
    Get price history for a product
    """
    try:
        monitoring_service = MonitoringService(db)
        
        # Get price history
        prices, stats = await monitoring_service.get_product_price_history(
            product_id=product_id,
            days=days,
            limit=limit
        )
        
        return PriceHistoryResponse(
            product_id=product_id,
            prices=prices,
            stats=stats,
            days=days
        )
        
    except Exception as e:
        logger.error(f"Failed to get price history for product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price history"
        )


@router.get("/stats/overview", response_model=MonitoringStatsResponse)
async def get_monitoring_stats(
    user_id: int = Query(..., description="Firebase-authenticated user id"),
    db: Session = Depends(get_db)
):
    """
    Get monitoring statistics overview
    """
    try:
        monitoring_service = MonitoringService(db)
        
        # Get stats for provided user_id (validated by Firebase at gateway)
        stats = await monitoring_service.get_user_monitoring_stats(user_id)
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get monitoring stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve monitoring statistics"
        )


@router.post("/check-alerts", response_model=dict)
async def check_price_alerts(
    product_id: Optional[int] = Query(None, description="Check alerts for specific product"),
    force: bool = Query(False, description="Force check even if recently checked"),
    db: Session = Depends(get_db)
):
    """
    Manually trigger price alert checking
    """
    try:
        alert_service = AlertService(db)
        
        # Check alerts
        result = await alert_service.check_price_alerts(
            product_id=product_id,
            force=force
        )
        
        logger.info(f"Checked price alerts: {result['checked_count']} alerts checked, {result['triggered_count']} triggered")
        return result
        
    except Exception as e:
        logger.error(f"Failed to check price alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check price alerts"
        )


@router.get("/trends/price-changes", response_model=List[dict])
async def get_price_change_trends(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    threshold_percentage: float = Query(5.0, ge=0.1, le=50.0, description="Minimum change percentage to include"),
    limit: int = Query(50, ge=1, le=200, description="Number of trends to return"),
    db: Session = Depends(get_db)
):
    """
    Get price change trends across all products
    """
    try:
        monitoring_service = MonitoringService(db)
        
        trends = await monitoring_service.get_price_change_trends(
            days=days,
            threshold_percentage=threshold_percentage,
            limit=limit
        )
        
        return trends
        
    except Exception as e:
        logger.error(f"Failed to get price change trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price change trends"
        )
