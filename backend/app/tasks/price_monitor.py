"""
Price monitoring background task (Firebase Firestore version)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from app.services.price_monitor_service import PriceMonitorService

logger = logging.getLogger(__name__)


class PriceMonitoringTask:
    """
    Background task for monitoring product prices using Firebase Firestore
    """

    def __init__(self):
        self.last_run = None
        self.is_running = False
        self.price_monitor = PriceMonitorService()

    # ---------------------------------------------------
    # Main Monitoring Runner
    # ---------------------------------------------------
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the Firestore-based price monitoring task
        """
        if self.is_running:
            logger.warning("Price monitoring task is already running")
            return {"status": "already_running"}

        try:
            self.is_running = True
            self.last_run = datetime.utcnow()
            logger.info("🚀 Starting Firestore price monitoring task")

            # Fetch products needing monitoring
            products = await self.price_monitor._get_products_for_monitoring()
            if not products:
                logger.info("No products need monitoring at this time.")
                return {
                    "status": "completed",
                    "products_monitored": 0,
                    "price_changes": 0,
                }

            logger.info(f"Monitoring {len(products)} products...")

            # Scrape product prices concurrently
            scrape_results = await self.price_monitor.scraping_service.scrape_multiple_products(
                products
            )

            # Process updates and trigger alerts
            await self.price_monitor._process_monitoring_results(scrape_results)

            # Gather stats after run
            stats = await self.price_monitor.get_monitoring_stats()
            logger.info(f"✅ Firestore price monitoring completed: {stats}")

            return {
                "status": "completed",
                "products_monitored": len(products),
                "stats": stats,
            }

        except Exception as e:
            logger.error(f"❌ Price monitoring task failed: {e}")
            return {"status": "failed", "error": str(e)}

        finally:
            self.is_running = False

    # ---------------------------------------------------
    # Manual Product Monitoring
    # ---------------------------------------------------
    async def monitor_specific_product(self, product_id: str) -> Dict[str, Any]:
        """
        Manually monitor a specific product in Firestore
        """
        try:
            result = await self.price_monitor.monitor_product(product_id)
            logger.info(f"Manually monitored product {product_id}: {result}")
            return {
                "status": "completed",
                "product_id": product_id,
                "result": result,
            }

        except Exception as e:
            logger.error(f"❌ Failed to monitor product {product_id}: {e}")
            return {
                "status": "failed",
                "product_id": product_id,
                "error": str(e),
            }

    # ---------------------------------------------------
    # Cleanup Task
    # ---------------------------------------------------
    async def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Remove old price and scraping data from Firestore
        """
        try:
            result = await self.price_monitor.cleanup_old_data(days_to_keep)
            logger.info(f"🧹 Cleaned up Firestore data older than {days_to_keep} days")
            return {"status": "completed", "result": result}

        except Exception as e:
            logger.error(f"❌ Failed to clean old data: {e}")
            return {"status": "failed", "error": str(e)}
