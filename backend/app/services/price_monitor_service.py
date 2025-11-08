"""
Price monitoring service for automated price tracking and alerting (Firebase Firestore version)
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from firebase_admin import firestore
from app.services.scraping_service import ScrapingService
from app.services.alert_service import AlertService
from config import settings

logger = logging.getLogger(__name__)
db = firestore.client()


class PriceMonitorService:
    """
    Firebase Firestore-based Service class for automated price monitoring and alerting
    """

    def __init__(self):
        self.products_ref = db.collection("products")
        self.prices_ref = db.collection("prices")
        self.alerts_ref = db.collection("alerts")
        self.scraping_service = ScrapingService()
        self.alert_service = AlertService()
        self.is_running = False
        self.monitoring_task = None

    # ---------------------------------
    # Start / Stop Monitoring Loop
    # ---------------------------------
    async def start_monitoring(self):
        """
        Start the Firestore-based price monitoring loop
        """
        if self.is_running:
            logger.warning("Price monitoring is already running")
            return

        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("✅ Firestore price monitoring started")

    async def stop_monitoring(self):
        """
        Stop the price monitoring loop
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
        logger.info("🛑 Firestore price monitoring stopped")

    # ---------------------------------
    # Core Monitoring Logic
    # ---------------------------------
    async def _monitoring_loop(self):
        """
        Periodically check tracked products and update their prices
        """
        while self.is_running:
            try:
                products = await self._get_products_for_monitoring()
                if products:
                    logger.info(f"🔎 Monitoring {len(products)} products...")

                    # Scrape product prices
                    results = await self.scraping_service.scrape_multiple_products(products)

                    # Process updated prices and trigger alerts
                    await self._process_monitoring_results(results)
                else:
                    logger.info("No products eligible for monitoring right now.")

                await asyncio.sleep(settings.PRICE_CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(60)

    async def _get_products_for_monitoring(self) -> List[Dict[str, Any]]:
        """
        Fetch products from Firestore that need to be monitored
        """
        try:
            cutoff = datetime.utcnow() - timedelta(seconds=settings.PRICE_CHECK_INTERVAL)
            products = []
            for doc in self.products_ref.where("is_tracking", "==", True).stream():
                p = doc.to_dict()
                last_updated = p.get("updated_at")
                if not last_updated or (
                    isinstance(last_updated, datetime) and last_updated < cutoff
                ):
                    products.append(p)
            return products[:100]  # Limit to prevent overload
        except Exception as e:
            logger.error(f"Failed to fetch products for monitoring: {e}")
            return []

    async def _process_monitoring_results(self, results: List[Dict[str, Any]]):
        """
        Process scraped results, update Firestore, and trigger alerts
        """
        try:
            for result in results:
                if not result.get("success"):
                    continue

                product_id = result.get("product_id")
                if not product_id:
                    continue

                product_ref = self.products_ref.document(product_id)
                product = product_ref.get()
                if not product.exists:
                    continue

                product_data = product.to_dict()
                price_changed = await self._check_price_change(product_data)

                # Update product record
                product_ref.update(
                    {
                        "updated_at": datetime.utcnow(),
                        "last_monitored": datetime.utcnow(),
                    }
                )

                # Trigger alerts if price changed
                if price_changed:
                    await self.alert_service.check_product_alerts(product_id)
        except Exception as e:
            logger.error(f"Failed to process monitoring results: {e}")

    async def _check_price_change(self, product: Dict[str, Any]) -> bool:
        """
        Check whether product price changed significantly
        """
        try:
            product_id = product["id"]
            current_price = product.get("current_price")
            if not current_price:
                return False

            # Fetch recent price history
            query = (
                self.prices_ref.where("product_id", "==", product_id)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(2)
            )
            docs = [doc.to_dict() for doc in query.stream()]
            if len(docs) < 2:
                return True  # First price record

            previous_price = docs[1]["price"]
            if not previous_price:
                return False

            change_percentage = abs(current_price - previous_price) / previous_price
            return change_percentage >= settings.PRICE_CHANGE_THRESHOLD

        except Exception as e:
            logger.error(f"Failed to check price change for {product.get('id')}: {e}")
            return False

    # ---------------------------------
    # Manual Monitoring
    # ---------------------------------
    async def monitor_product(self, product_id: str) -> Dict[str, Any]:
        """
        Manually monitor a single product by ID
        """
        try:
            doc = self.products_ref.document(product_id).get()
            if not doc.exists:
                return {"success": False, "error": "Product not found"}

            product = doc.to_dict()
            result = await self.scraping_service.scrape_product(product, force=True)

            if result.get("success"):
                price_changed = await self._check_price_change(product)
                if price_changed:
                    await self.alert_service.check_product_alerts(product_id)
                return {
                    "success": True,
                    "price_changed": price_changed,
                    "current_price": product.get("current_price"),
                }

            return result
        except Exception as e:
            logger.error(f"Failed to monitor product {product_id}: {e}")
            return {"success": False, "error": str(e)}

    # ---------------------------------
    # Monitoring Statistics
    # ---------------------------------
    async def get_monitoring_stats(self) -> Dict[str, Any]:
        """
        Gather global monitoring statistics from Firestore
        """
        try:
            products = [doc.to_dict() for doc in self.products_ref.stream()]
            alerts = [doc.to_dict() for doc in self.alerts_ref.stream()]
            prices = [doc.to_dict() for doc in self.prices_ref.stream()]

            total_products = len(products)
            tracking_products = len([p for p in products if p.get("is_tracking")])
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_changes = len(
                [
                    pr
                    for pr in prices
                    if pr.get("created_at")
                    and isinstance(pr["created_at"], datetime)
                    and pr["created_at"] >= recent_cutoff
                ]
            )
            active_alerts = len([a for a in alerts if a.get("is_active")])
            triggered_today = len(
                [
                    a
                    for a in alerts
                    if a.get("is_triggered")
                    and a.get("triggered_at")
                    and str(datetime.utcnow().date()) in str(a["triggered_at"])
                ]
            )

            return {
                "total_products": total_products,
                "tracking_products": tracking_products,
                "recent_price_changes": recent_changes,
                "active_alerts": active_alerts,
                "triggered_today": triggered_today,
                "monitoring_status": "running" if self.is_running else "stopped",
            }

        except Exception as e:
            logger.error(f"Failed to get monitoring stats: {e}")
            return {}

    # ---------------------------------
    # Cleanup Old Data
    # ---------------------------------
    async def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Delete old price and scraping data from Firestore
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            deleted_prices = 0

            for doc in self.prices_ref.stream():
                data = doc.to_dict()
                created_at = data.get("created_at")
                if created_at and isinstance(created_at, datetime) and created_at < cutoff_date:
                    self.prices_ref.document(doc.id).delete()
                    deleted_prices += 1

            logger.info(f"🧹 Deleted {deleted_prices} old price records")
            return {
                "old_prices_deleted": deleted_prices,
                "cutoff_date": cutoff_date.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to clean old data: {e}")
            raise
