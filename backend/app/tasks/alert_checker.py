"""
Alert checking background task (Firebase Firestore version)
"""

import logging
from datetime import datetime
from typing import Dict, Any
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)


class AlertCheckingTask:
    """
    Background task for checking price alerts in Firestore
    """

    def __init__(self):
        self.last_run = None
        self.is_running = False
        self.alert_service = AlertService()

    # ---------------------------------------------------
    # Run periodic alert check
    # ---------------------------------------------------
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the alert checking task across all users and products
        """
        if self.is_running:
            logger.warning("⚠️ Alert checking task is already running")
            return {"status": "already_running"}

        try:
            self.is_running = True
            self.last_run = datetime.utcnow()
            logger.info("🔔 Starting Firestore alert checking task")

            result = await self.alert_service.check_price_alerts(force=False)

            logger.info(f"✅ Alert checking completed: {result}")
            return {
                "status": "completed",
                "checked_count": result.get("checked_count", 0),
                "triggered_count": result.get("triggered_count", 0),
                "success": result.get("success", True),
            }

        except Exception as e:
            logger.error(f"❌ Alert checking task failed: {e}")
            return {"status": "failed", "error": str(e)}

        finally:
            self.is_running = False

    # ---------------------------------------------------
    # Check alerts for a specific product
    # ---------------------------------------------------
    async def check_product_alerts(self, product_id: str) -> Dict[str, Any]:
        """
        Check and trigger alerts for a specific Firestore product
        """
        try:
            logger.info(f"🔎 Checking alerts for product {product_id}")
            result = await self.alert_service.check_product_alerts(product_id)
            return {
                "status": "completed",
                "product_id": product_id,
                "triggered_alerts": len(result),
                "alerts": result,
            }
        except Exception as e:
            logger.error(f"❌ Failed to check alerts for product {product_id}: {e}")
            return {
                "status": "failed",
                "product_id": product_id,
                "error": str(e),
            }

    # ---------------------------------------------------
    # Get Alert Stats
    # ---------------------------------------------------
    async def get_alert_stats(self, user_id: str = None) -> Dict[str, Any]:
        """
        Get alert statistics from Firestore
        """
        try:
            stats = await self.alert_service.get_alert_stats(user_id)
            return {"status": "completed", "stats": stats}
        except Exception as e:
            logger.error(f"Failed to get alert stats: {e}")
            return {"status": "failed", "error": str(e)}
