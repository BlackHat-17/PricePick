"""
Alert checking background task
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from app.database import get_db_session
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)


class AlertCheckingTask:
    """
    Background task for checking price alerts
    """
    
    def __init__(self):
        self.last_run = None
        self.is_running = False
    
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the alert checking task
        """
        if self.is_running:
            logger.warning("Alert checking task is already running")
            return {"status": "already_running"}
        
        try:
            self.is_running = True
            self.last_run = datetime.utcnow()
            
            logger.info("Starting alert checking task")
            
            # Get database session
            db = get_db_session()
            try:
                # Initialize alert service
                alert_service = AlertService(db)
                
                # Check all price alerts
                result = await alert_service.check_price_alerts(force=False)
                
                logger.info(f"Alert checking completed: {result}")
                
                return {
                    "status": "completed",
                    "checked_count": result.get("checked_count", 0),
                    "triggered_count": result.get("triggered_count", 0),
                    "success": result.get("success", False)
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Alert checking task failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
        finally:
            self.is_running = False
    
    async def check_product_alerts(self, product_id: int) -> Dict[str, Any]:
        """
        Check alerts for a specific product
        """
        try:
            db = get_db_session()
            try:
                alert_service = AlertService(db)
                result = await alert_service.check_product_alerts(product_id)
                
                return {
                    "status": "completed",
                    "product_id": product_id,
                    "triggered_alerts": len(result),
                    "alerts": result
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to check alerts for product {product_id}: {str(e)}")
            return {
                "status": "failed",
                "product_id": product_id,
                "error": str(e)
            }
    
    async def get_alert_stats(self, user_id: int = None) -> Dict[str, Any]:
        """
        Get alert statistics
        """
        try:
            db = get_db_session()
            try:
                alert_service = AlertService(db)
                stats = await alert_service.get_alert_stats(user_id)
                
                return {
                    "status": "completed",
                    "stats": stats
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to get alert stats: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
