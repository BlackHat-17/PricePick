"""
Alert service for managing price alerts and notifications
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.models.monitoring import PriceAlert
from app.models.product import Product
from app.models.price import Price
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class AlertService:
    """
    Service class for managing price alerts and notifications
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
    
    async def create_alert(self, user_id: int, alert_data) -> PriceAlert:
        """
        Create a new price alert
        """
        try:
            # Validate product exists
            product = self.db.query(Product).filter(
                Product.id == alert_data.product_id,
                Product.is_active == True
            ).first()
            
            if not product:
                raise ValueError("Product not found")
            
            # Create alert
            alert = PriceAlert(
                user_id=user_id,
                product_id=alert_data.product_id,
                alert_type=alert_data.alert_type,
                target_price=alert_data.target_price,
                threshold_percentage=alert_data.threshold_percentage,
                threshold_amount=alert_data.threshold_amount,
                notify_email=alert_data.notify_email,
                notify_push=alert_data.notify_push,
                notify_sms=alert_data.notify_sms,
                notes=alert_data.notes,
                extra_metadata=alert_data.metadata
            )
            
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)
            
            logger.info(f"Created price alert {alert.id} for user {user_id}")
            return alert
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create alert: {str(e)}")
            raise
    
    async def get_alert(self, alert_id: int) -> Optional[PriceAlert]:
        """
        Get an alert by ID
        """
        try:
            return self.db.query(PriceAlert).filter(
                PriceAlert.id == alert_id,
                PriceAlert.is_active == True
            ).first()
        except Exception as e:
            logger.error(f"Failed to get alert {alert_id}: {str(e)}")
            raise
    
    async def list_user_alerts(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[PriceAlert]:
        """
        List alerts for a user
        """
        try:
            query = self.db.query(PriceAlert).filter(
                PriceAlert.user_id == user_id,
                PriceAlert.is_active == True
            )
            
            # Apply filters
            if filters:
                if filters.get("is_active") is not None:
                    query = query.filter(PriceAlert.is_active == filters["is_active"])
                
                if filters.get("alert_type"):
                    query = query.filter(PriceAlert.alert_type == filters["alert_type"])
                
                if filters.get("product_id"):
                    query = query.filter(PriceAlert.product_id == filters["product_id"])
            
            return query.offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to list alerts for user {user_id}: {str(e)}")
            raise
    
    async def update_alert(self, alert_id: int, alert_data) -> Optional[PriceAlert]:
        """
        Update an alert
        """
        try:
            alert = await self.get_alert(alert_id)
            if not alert:
                return None
            
            # Update fields
            update_data = alert_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(alert, field):
                    setattr(alert, field, value)
            
            self.db.commit()
            self.db.refresh(alert)
            
            logger.info(f"Updated alert {alert_id}")
            return alert
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update alert {alert_id}: {str(e)}")
            raise
    
    async def delete_alert(self, alert_id: int) -> bool:
        """
        Delete an alert (soft delete)
        """
        try:
            alert = await self.get_alert(alert_id)
            if not alert:
                return False
            
            alert.is_active = False
            self.db.commit()
            
            logger.info(f"Deleted alert {alert_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete alert {alert_id}: {str(e)}")
            raise
    
    async def toggle_alert(self, alert_id: int, is_active: bool) -> bool:
        """
        Toggle alert active status
        """
        try:
            alert = await self.get_alert(alert_id)
            if not alert:
                return False
            
            alert.is_active = is_active
            self.db.commit()
            
            logger.info(f"Toggled alert {alert_id}: {is_active}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to toggle alert {alert_id}: {str(e)}")
            raise
    
    async def check_price_alerts(self, product_id: Optional[int] = None, force: bool = False) -> Dict[str, Any]:
        """
        Check all price alerts and trigger notifications
        """
        try:
            # Get alerts to check
            if product_id:
                alerts = self.db.query(PriceAlert).filter(
                    PriceAlert.product_id == product_id,
                    PriceAlert.is_active == True
                ).all()
            else:
                alerts = self.db.query(PriceAlert).filter(
                    PriceAlert.is_active == True
                ).all()
            
            checked_count = 0
            triggered_count = 0
            
            for alert in alerts:
                try:
                    # Check if alert should be checked
                    if not force and not self._should_check_alert(alert):
                        continue
                    
                    # Get current product price
                    product = self.db.query(Product).filter(
                        Product.id == alert.product_id
                    ).first()
                    
                    if not product or not product.current_price:
                        continue
                    
                    # Check if alert should trigger
                    if alert.should_trigger(product.current_price):
                        # Trigger alert
                        await self._trigger_alert(alert, product)
                        triggered_count += 1
                    
                    # Update last checked time
                    alert.last_checked = datetime.utcnow().isoformat()
                    checked_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to check alert {alert.id}: {str(e)}")
                    continue
            
            self.db.commit()
            
            logger.info(f"Checked {checked_count} alerts, triggered {triggered_count}")
            return {
                "checked_count": checked_count,
                "triggered_count": triggered_count,
                "success": True
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to check price alerts: {str(e)}")
            raise
    
    async def check_product_alerts(self, product_id: int) -> List[Dict[str, Any]]:
        """
        Check alerts for a specific product
        """
        try:
            # Get product
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product or not product.current_price:
                return []
            
            # Get active alerts for this product
            alerts = self.db.query(PriceAlert).filter(
                PriceAlert.product_id == product_id,
                PriceAlert.is_active == True
            ).all()
            
            triggered_alerts = []
            
            for alert in alerts:
                try:
                    if alert.should_trigger(product.current_price):
                        # Trigger alert
                        result = await self._trigger_alert(alert, product)
                        triggered_alerts.append(result)
                    
                    # Update last checked time
                    alert.last_checked = datetime.utcnow().isoformat()
                    
                except Exception as e:
                    logger.error(f"Failed to check alert {alert.id}: {str(e)}")
                    continue
            
            self.db.commit()
            return triggered_alerts
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to check product alerts for {product_id}: {str(e)}")
            raise
    
    def _should_check_alert(self, alert: PriceAlert) -> bool:
        """
        Check if an alert should be checked now
        """
        if not alert.last_checked:
            return True
        
        try:
            last_checked = datetime.fromisoformat(alert.last_checked.replace('Z', '+00:00'))
            time_since_check = datetime.utcnow() - last_checked
            
            # Check every hour for active alerts
            return time_since_check.total_seconds() >= 3600
            
        except (ValueError, TypeError):
            return True
    
    async def _trigger_alert(self, alert: PriceAlert, product: Product) -> Dict[str, Any]:
        """
        Trigger an alert and send notifications
        """
        try:
            # Mark alert as triggered
            alert.trigger()
            
            # Get price history for context
            previous_price = self.db.query(Price).filter(
                Price.product_id == product.id
            ).order_by(Price.created_at.desc()).offset(1).first()
            
            # Prepare notification data
            notification_data = {
                "alert_id": alert.id,
                "product_id": product.id,
                "product_name": product.name,
                "product_url": product.product_url,
                "current_price": product.current_price,
                "previous_price": previous_price.price if previous_price else product.current_price,
                "alert_type": alert.alert_type,
                "target_price": alert.target_price,
                "currency": product.currency
            }
            
            # Calculate savings/increase
            if previous_price and previous_price.price:
                change_amount = product.current_price - previous_price.price
                change_percentage = (change_amount / previous_price.price) * 100
                
                notification_data.update({
                    "change_amount": change_amount,
                    "change_percentage": change_percentage,
                    "savings": abs(change_amount) if change_amount < 0 else 0,
                    "increase": change_amount if change_amount > 0 else 0
                })
            
            # Send notifications
            if alert.notify_email:
                await self.notification_service.send_email_alert(alert, notification_data)
            
            if alert.notify_push:
                await self.notification_service.send_push_alert(alert, notification_data)
            
            if alert.notify_sms:
                await self.notification_service.send_sms_alert(alert, notification_data)
            
            logger.info(f"Triggered alert {alert.id} for product {product.id}")
            
            return {
                "alert_id": alert.id,
                "product_id": product.id,
                "triggered_at": datetime.utcnow().isoformat(),
                "notifications_sent": {
                    "email": alert.notify_email,
                    "push": alert.notify_push,
                    "sms": alert.notify_sms
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to trigger alert {alert.id}: {str(e)}")
            raise
    
    async def get_alert_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get alert statistics
        """
        try:
            query = self.db.query(PriceAlert)
            
            if user_id:
                query = query.filter(PriceAlert.user_id == user_id)
            
            total_alerts = query.count()
            active_alerts = query.filter(PriceAlert.is_active == True).count()
            triggered_alerts = query.filter(PriceAlert.is_triggered == True).count()
            
            # Count by type
            price_drop_alerts = query.filter(PriceAlert.alert_type == "price_drop").count()
            price_increase_alerts = query.filter(PriceAlert.alert_type == "price_increase").count()
            target_price_alerts = query.filter(PriceAlert.alert_type == "target_price").count()
            
            return {
                "total_alerts": total_alerts,
                "active_alerts": active_alerts,
                "triggered_alerts": triggered_alerts,
                "by_type": {
                    "price_drop": price_drop_alerts,
                    "price_increase": price_increase_alerts,
                    "target_price": target_price_alerts
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get alert stats: {str(e)}")
            return {}
