"""
Price monitoring and alerting API routes (Firebase Firestore version)
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime, timedelta

from app.schemas.monitoring import (
    PriceAlertCreate,
    PriceAlertUpdate,
    PriceAlertResponse,
    PriceHistoryResponse,
    MonitoringStatsResponse,
)
from app.services.alert_service import AlertService
from app.services.monitoring_service import MonitoringService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
alert_service = AlertService()
monitoring_service = MonitoringService()


@router.post("/alerts", response_model=PriceAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_price_alert(
    alert_data: PriceAlertCreate,
    user_id: str = Query(..., description="Firebase-authenticated user UID"),
):
    """
    Create a new price alert for a Firebase user
    """
    try:
        alert = await alert_service.create_alert(user_id, alert_data)
        logger.info(f"Created price alert for user {user_id}")
        return alert
    except Exception as e:
        logger.error(f"Failed to create price alert: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/alerts", response_model=List[PriceAlertResponse])
async def list_price_alerts(
    user_id: str = Query(...),
    is_active: Optional[bool] = None,
    alert_type: Optional[str] = None,
    product_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
):
    """
    List price alerts for a Firebase user
    """
    try:
        filters = {
            "is_active": is_active,
            "alert_type": alert_type,
            "product_id": product_id,
        }
        alerts = await alert_service.list_user_alerts(user_id, skip, limit, filters)
        return alerts
    except Exception as e:
        logger.error(f"Failed to list price alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve price alerts")


@router.get("/alerts/{alert_id}", response_model=PriceAlertResponse)
async def get_price_alert(alert_id: str, user_id: str = Query(...)):
    """
    Get a specific price alert
    """
    alert = await alert_service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Price alert not found")
    if alert.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return alert


@router.put("/alerts/{alert_id}", response_model=PriceAlertResponse)
async def update_price_alert(
    alert_id: str, alert_data: PriceAlertUpdate, user_id: str = Query(...)
):
    """
    Update an existing price alert
    """
    alert = await alert_service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Price alert not found")
    if alert.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    updated = await alert_service.update_alert(alert_id, alert_data)
    return updated


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_price_alert(alert_id: str, user_id: str = Query(...)):
    """
    Delete a price alert
    """
    alert = await alert_service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Price alert not found")
    if alert.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    await alert_service.delete_alert(alert_id)
    logger.info(f"Deleted price alert {alert_id}")


@router.post("/alerts/{alert_id}/toggle", response_model=dict)
async def toggle_price_alert(alert_id: str, user_id: str = Query(...)):
    """
    Toggle price alert active status
    """
    alert = await alert_service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    new_status = not alert.get("is_active", True)
    await alert_service.toggle_alert(alert_id, new_status)

    return {
        "alert_id": alert_id,
        "is_active": new_status,
        "message": f"Alert {'activated' if new_status else 'deactivated'}",
    }


@router.get("/history/{product_id}", response_model=PriceHistoryResponse)
async def get_price_history(
    product_id: str,
    days: int = 30,
    limit: int = 100,
):
    """
    Get price history for a product (from Firestore)
    """
    prices, stats = await monitoring_service.get_product_price_history(
        product_id, days, limit
    )
    return PriceHistoryResponse(
        product_id=product_id, prices=prices, stats=stats, days=days
    )


@router.get("/stats/overview", response_model=MonitoringStatsResponse)
async def get_monitoring_stats(user_id: str = Query(...)):
    """
    Get monitoring statistics for a Firebase user
    """
    stats = await monitoring_service.get_user_monitoring_stats(user_id)
    return stats


@router.post("/check-alerts", response_model=dict)
async def check_price_alerts(
    product_id: Optional[str] = None,
    force: bool = False,
):
    """
    Manually trigger alert checks (Firestore version)
    """
    result = await alert_service.check_price_alerts(product_id, force)
    return result


@router.get("/trends/price-changes", response_model=List[dict])
async def get_price_change_trends(
    days: int = 7, threshold_percentage: float = 5.0, limit: int = 50
):
    """
    Get price change trends across all products (Firestore)
    """
    trends = await monitoring_service.get_price_change_trends(
        days, threshold_percentage, limit
    )
    return trends
