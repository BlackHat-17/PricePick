"""
Price monitoring service for automated price tracking and alerting
"""

import asyncio
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.models.product import Product
from app.models.price import Price
from app.models.monitoring import PriceAlert, PriceHistory
from app.services.scraping_service import ScrapingService
from app.services.alert_service import AlertService
from config import settings

logger = logging.getLogger(__name__)


class PriceMonitorService:
    """
    Service class for automated price monitoring and alerting
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.scraping_service = ScrapingService(db)
        self.alert_service = AlertService(db)
        self.is_running = False
        self.monitoring_task = None
    
    async def start_monitoring(self):
        """
        Start the price monitoring service
        """
        if self.is_running:
            logger.warning("Price monitoring is already running")
            return
        
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Price monitoring service started")
    
    async def stop_monitoring(self):
        """
        Stop the price monitoring service
        """
        if not self.is_running:
            logger.warning("Price monitoring is not running")
            return
        
        self.is_running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Price monitoring service stopped")
    
    async def _monitoring_loop(self):
        """
        Main monitoring loop
        """
        while self.is_running:
            try:
                # Get products that need monitoring
                products = await self._get_products_for_monitoring()
                
                if products:
                    logger.info(f"Monitoring {len(products)} products")
                    
                    # Scrape products
                    results = await self.scraping_service.scrape_multiple_products(products)
                    
                    # Process results and check alerts
                    await self._process_monitoring_results(results)
                
                # Wait before next monitoring cycle
                await asyncio.sleep(settings.PRICE_CHECK_INTERVAL)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _get_products_for_monitoring(self) -> List[Product]:
        """
        Get products that need to be monitored
        """
        try:
            # Get products that are tracking and haven't been checked recently
            cutoff_time = datetime.utcnow() - timedelta(seconds=settings.PRICE_CHECK_INTERVAL)
            
            products = self.db.query(Product).filter(
                Product.is_active == True,
                Product.is_tracking == True,
                Product.updated_at < cutoff_time
            ).limit(100).all()  # Limit to prevent overwhelming the system
            
            return products
            
        except Exception as e:
            logger.error(f"Failed to get products for monitoring: {str(e)}")
            return []
    
    async def _process_monitoring_results(self, results: List[Dict[str, Any]]):
        """
        Process monitoring results and trigger alerts
        """
        try:
            for result in results:
                if not result.get("success"):
                    continue
                
                product_id = result.get("product_id")
                if not product_id:
                    continue
                
                # Get the product
                product = self.db.query(Product).filter(Product.id == product_id).first()
                if not product:
                    continue
                
                # Check if price changed significantly
                if await self._check_price_change(product):
                    # Trigger alerts
                    await self.alert_service.check_product_alerts(product_id)
                
                # Update product tracking info
                product.last_monitored = datetime.utcnow()
                self.db.commit()
                
        except Exception as e:
            logger.error(f"Failed to process monitoring results: {str(e)}")
    
    async def _check_price_change(self, product: Product) -> bool:
        """
        Check if product price has changed significantly
        """
        try:
            # Get current and previous prices
            current_price = product.current_price
            if not current_price:
                return False
            
            previous_price = self.db.query(Price).filter(
                Price.product_id == product.id
            ).order_by(Price.created_at.desc()).offset(1).first()
            
            if not previous_price:
                return True  # First price, consider it a change
            
            # Calculate change percentage
            change_percentage = abs(current_price - previous_price.price) / previous_price.price
            
            return change_percentage >= settings.PRICE_CHANGE_THRESHOLD
            
        except Exception as e:
            logger.error(f"Failed to check price change for product {product.id}: {str(e)}")
            return False
    
    async def monitor_product(self, product_id: int) -> Dict[str, Any]:
        """
        Manually monitor a specific product
        """
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {"success": False, "error": "Product not found"}
            
            # Scrape product
            result = await self.scraping_service.scrape_product(product, force=True)
            
            if result["success"]:
                # Check for price changes
                price_changed = await self._check_price_change(product)
                
                # Check alerts
                if price_changed:
                    await self.alert_service.check_product_alerts(product_id)
                
                return {
                    "success": True,
                    "price_changed": price_changed,
                    "current_price": product.current_price,
                    "result": result
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Failed to monitor product {product_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_monitoring_stats(self) -> Dict[str, Any]:
        """
        Get monitoring statistics
        """
        try:
            # Count products being monitored
            total_products = self.db.query(Product).filter(Product.is_active == True).count()
            tracking_products = self.db.query(Product).filter(
                Product.is_active == True,
                Product.is_tracking == True
            ).count()
            
            # Count recent price changes
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_changes = self.db.query(Price).filter(
                Price.created_at >= recent_cutoff
            ).count()
            
            # Count active alerts
            active_alerts = self.db.query(PriceAlert).filter(
                PriceAlert.is_active == True
            ).count()
            
            # Count triggered alerts today
            today = datetime.utcnow().date()
            triggered_today = self.db.query(PriceAlert).filter(
                PriceAlert.is_triggered == True,
                PriceAlert.triggered_at.like(f"{today}%")
            ).count()
            
            return {
                "total_products": total_products,
                "tracking_products": tracking_products,
                "recent_price_changes": recent_changes,
                "active_alerts": active_alerts,
                "triggered_today": triggered_today,
                "monitoring_status": "running" if self.is_running else "stopped"
            }
            
        except Exception as e:
            logger.error(f"Failed to get monitoring stats: {str(e)}")
            return {}
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Clean up old monitoring data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Clean up old price history
            old_prices = self.db.query(Price).filter(
                Price.created_at < cutoff_date
            ).count()
            
            self.db.query(Price).filter(
                Price.created_at < cutoff_date
            ).delete()
            
            # Clean up old scraping sessions
            old_sessions = self.db.query(ScrapingSession).filter(
                ScrapingSession.created_at < cutoff_date
            ).count()
            
            self.db.query(ScrapingSession).filter(
                ScrapingSession.created_at < cutoff_date
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Cleaned up {old_prices} old prices and {old_sessions} old sessions")
            
            return {
                "old_prices_deleted": old_prices,
                "old_sessions_deleted": old_sessions,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cleanup old data: {str(e)}")
            raise
