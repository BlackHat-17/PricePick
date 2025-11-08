"""
Alert service for managing price alerts and notifications (Firestore version)
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from firebase_admin import firestore

from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
db = firestore.client()


class AlertService:
    """
    Service class for managing price alerts and notifications using Firestore
    """
class AlertService:
    """
    Service class for managing price alerts and notifications using Firestore
    """

    def __init__(self):
        from app.firebase import db  # ✅ ensure initialized once and reused
        self.db = db
        self.notification_service = NotificationService(db)  # ✅ pass db here
        self.alerts_ref = db.collection("alerts")
        self.products_ref = db.collection("products")

    # ---------------------------------------------------
    # Create & Retrieve Alerts
    # ---------------------------------------------------
    async def create_alert(self, user_id: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new price alert for a user
        """
        try:
            # Verify product exists
            product_ref = self.products_ref.document(alert_data["product_id"])
            product_doc = product_ref.get()
            if not product_doc.exists:
                raise ValueError("Product not found")

            alert = {
                "user_id": user_id,
                "product_id": alert_data["product_id"],
                "alert_type": alert_data["alert_type"],
                "target_price": alert_data.get("target_price"),
                "threshold_percentage": alert_data.get("threshold_percentage"),
                "notify_email": alert_data.get("notify_email", True),
                "notify_push": alert_data.get("notify_push", False),
                "notify_sms": alert_data.get("notify_sms", False),
                "notes": alert_data.get("notes", ""),
                "is_active": True,
                "is_triggered": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_checked": None,
            }

            alert_ref = self.alerts_ref.document()
            alert_ref.set(alert)

            logger.info(f"✅ Created alert {alert_ref.id} for user {user_id}")
            return {"id": alert_ref.id, **alert}

        except Exception as e:
            logger.error(f"❌ Failed to create alert: {e}")
            raise

    async def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific alert by ID
        """
        try:
            doc = self.alerts_ref.document(alert_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Failed to fetch alert {alert_id}: {e}")
            raise

    async def list_user_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all active alerts for a user
        """
        try:
            alerts = self.alerts_ref.where("user_id", "==", user_id).where("is_active", "==", True).stream()
            return [doc.to_dict() | {"id": doc.id} for doc in alerts]
        except Exception as e:
            logger.error(f"Failed to list alerts for {user_id}: {e}")
            raise

    # ---------------------------------------------------
    # Update, Toggle, and Delete Alerts
    # ---------------------------------------------------
    async def update_alert(self, alert_id: str, alert_data: Dict[str, Any]) -> bool:
        try:
            update_data = {**alert_data, "updated_at": datetime.utcnow()}
            self.alerts_ref.document(alert_id).update(update_data)
            logger.info(f"Updated alert {alert_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update alert {alert_id}: {e}")
            return False

    async def toggle_alert(self, alert_id: str, is_active: bool) -> bool:
        try:
            self.alerts_ref.document(alert_id).update({"is_active": is_active, "updated_at": datetime.utcnow()})
            logger.info(f"Toggled alert {alert_id} to {is_active}")
            return True
        except Exception as e:
            logger.error(f"Failed to toggle alert {alert_id}: {e}")
            return False

    async def delete_alert(self, alert_id: str) -> bool:
        try:
            self.alerts_ref.document(alert_id).delete()
            logger.info(f"Deleted alert {alert_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete alert {alert_id}: {e}")
            return False

    # ---------------------------------------------------
    # Core Alert Checking Logic
    # ---------------------------------------------------
    async def check_price_alerts(self, product_id: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """
        Check all active price alerts and trigger notifications if needed
        """
        try:
            if product_id:
                alerts = self.alerts_ref.where("product_id", "==", product_id).where("is_active", "==", True).stream()
            else:
                alerts = self.alerts_ref.where("is_active", "==", True).stream()

            checked_count = 0
            triggered_count = 0

            for alert_doc in alerts:
                alert = alert_doc.to_dict()
                alert_id = alert_doc.id

                if not force and not self._should_check_alert(alert):
                    continue

                product_doc = self.products_ref.document(alert["product_id"]).get()
                if not product_doc.exists:
                    continue

                product = product_doc.to_dict()
                current_price = product.get("current_price")
                if current_price is None:
                    continue

                # Determine trigger condition
                if await self._should_trigger(alert, current_price):
                    await self._trigger_alert(alert_id, alert, product)
                    triggered_count += 1

                # Update last_checked
                self.alerts_ref.document(alert_id).update({"last_checked": datetime.utcnow()})
                checked_count += 1

            logger.info(f"Checked {checked_count} alerts, triggered {triggered_count}")
            return {
                "checked_count": checked_count,
                "triggered_count": triggered_count,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Failed to check price alerts: {e}")
            return {"success": False, "error": str(e)}

    async def check_product_alerts(self, product_id: str) -> List[Dict[str, Any]]:
        """
        Check and trigger alerts for a single product
        """
        try:
            product_doc = self.products_ref.document(product_id).get()
            if not product_doc.exists:
                return []

            product = product_doc.to_dict()
            current_price = product.get("current_price")
            if current_price is None:
                return []

            alerts = self.alerts_ref.where("product_id", "==", product_id).where("is_active", "==", True).stream()

            triggered_alerts = []
            for alert_doc in alerts:
                alert = alert_doc.to_dict()
                alert_id = alert_doc.id

                if await self._should_trigger(alert, current_price):
                    result = await self._trigger_alert(alert_id, alert, product)
                    triggered_alerts.append(result)

            return triggered_alerts
        except Exception as e:
            logger.error(f"Failed to check product alerts for {product_id}: {e}")
            return []

    # ---------------------------------------------------
    # Helper Methods
    # ---------------------------------------------------
    def _should_check_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Determine if an alert should be checked (every 60 mins)
        """
        last_checked = alert.get("last_checked")
        if not last_checked:
            return True

        if isinstance(last_checked, datetime):
            time_since = datetime.utcnow() - last_checked
            return time_since.total_seconds() >= 3600
        return True

    async def _should_trigger(self, alert: Dict[str, Any], current_price: float) -> bool:
        """
        Evaluate alert condition
        """
        alert_type = alert.get("alert_type")
        target_price = alert.get("target_price")
        threshold = alert.get("threshold_percentage")

        if alert_type == "target_price" and target_price is not None:
            return current_price <= target_price

        if alert_type == "price_drop" and threshold is not None:
            return current_price <= (1 - threshold / 100) * alert.get("previous_price", current_price)

        if alert_type == "price_increase" and threshold is not None:
            return current_price >= (1 + threshold / 100) * alert.get("previous_price", current_price)

        return False

    async def _trigger_alert(self, alert_id: str, alert: Dict[str, Any], product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger an alert and send notifications
        """
        try:
            now = datetime.utcnow()
            alert_update = {
                "is_triggered": True,
                "triggered_at": now,
                "updated_at": now,
            }
            self.alerts_ref.document(alert_id).update(alert_update)

            notification_data = {
                "alert_id": alert_id,
                "product_id": alert["product_id"],
                "product_name": product.get("name"),
                "product_url": product.get("product_url"),
                "current_price": product.get("current_price"),
                "alert_type": alert.get("alert_type"),
                "target_price": alert.get("target_price"),
                "currency": product.get("currency", "USD"),
                "triggered_at": now.isoformat(),
            }

            # Send notifications
            if alert.get("notify_email"):
                await self.notification_service.send_email_alert(alert, notification_data)
            if alert.get("notify_push"):
                await self.notification_service.send_push_alert(alert, notification_data)
            if alert.get("notify_sms"):
                await self.notification_service.send_sms_alert(alert, notification_data)

            logger.info(f"🔔 Triggered alert {alert_id} for product {alert['product_id']}")
            return notification_data

        except Exception as e:
            logger.error(f"Failed to trigger alert {alert_id}: {e}")
            return {}

    async def get_alert_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Compute alert statistics for all users or a specific user
        """
        try:
            if user_id:
                alerts = self.alerts_ref.where("user_id", "==", user_id).stream()
            else:
                alerts = self.alerts_ref.stream()

            total_alerts = 0
            active_alerts = 0
            triggered_alerts = 0
            by_type = {"price_drop": 0, "price_increase": 0, "target_price": 0}

            for doc in alerts:
                alert = doc.to_dict()
                total_alerts += 1
                if alert.get("is_active"):
                    active_alerts += 1
                if alert.get("is_triggered"):
                    triggered_alerts += 1
                if alert.get("alert_type") in by_type:
                    by_type[alert["alert_type"]] += 1

            return {
                "total_alerts": total_alerts,
                "active_alerts": active_alerts,
                "triggered_alerts": triggered_alerts,
                "by_type": by_type,
            }

        except Exception as e:
            logger.error(f"Failed to compute alert stats: {e}")
            return {}
