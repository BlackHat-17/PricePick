"""
Price monitoring background task
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from app.database import get_db_session
from app.services.price_monitor import PriceMonitorService

logger = logging.getLogger(__name__)


class PriceMonitoringTask:
    """
    Background task for monitoring product prices
    """
    
    def __init__(self):
        self.last_run = None
        self.is_running = False
    
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the price monitoring task
        """
        if self.is_running:
            logger.warning("Price monitoring task is already running")
            return {"status": "already_running"}
        
        try:
            self.is_running = True
            self.last_run = datetime.utcnow()
            
            logger.info("Starting price monitoring task")
            
            # Get database session
            db = get_db_session()
            try:
                # Initialize price monitor service
                price_monitor = PriceMonitorService(db)
                
                # Get products that need monitoring
                products = await price_monitor._get_products_for_monitoring()
                
                if not products:
                    logger.info("No products need monitoring")
                    return {
                        "status": "completed",
                        "products_monitored": 0,
                        "price_changes": 0
                    }
                
                logger.info(f"Monitoring {len(products)} products")
                
                # Monitor products
                results = await price_monitor._process_monitoring_results(
                    await price_monitor.scraping_service.scrape_multiple_products(products)
                )
                
                # Get monitoring stats
                stats = await price_monitor.get_monitoring_stats()
                
                logger.info(f"Price monitoring completed: {stats}")
                
                return {
                    "status": "completed",
                    "products_monitored": len(products),
                    "stats": stats
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Price monitoring task failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
        finally:
            self.is_running = False
    
    async def monitor_specific_product(self, product_id: int) -> Dict[str, Any]:
        """
        Monitor a specific product
        """
        try:
            db = get_db_session()
            try:
                price_monitor = PriceMonitorService(db)
                result = await price_monitor.monitor_product(product_id)
                
                return {
                    "status": "completed",
                    "product_id": product_id,
                    "result": result
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to monitor product {product_id}: {str(e)}")
            return {
                "status": "failed",
                "product_id": product_id,
                "error": str(e)
            }
    
    async def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Clean up old monitoring data
        """
        try:
            db = get_db_session()
            try:
                price_monitor = PriceMonitorService(db)
                result = await price_monitor.cleanup_old_data(days_to_keep)
                
                return {
                    "status": "completed",
                    "result": result
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
