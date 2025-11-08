"""
Price service for managing price data and statistics (Firebase Firestore version)
"""

from firebase_admin import firestore
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import logging

logger = logging.getLogger(__name__)
db = firestore.client()


class PriceService:
    """
    Firebase Firestore-based Price Service
    """

    def __init__(self):
        self.prices_ref = db.collection("prices")
        self.products_ref = db.collection("products")

    # -----------------------------
    # List Prices
    # -----------------------------
    async def list_prices(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List prices with filtering and pagination (Firestore)
        """
        try:
            query = self.prices_ref
            if filters:
                if filters.get("product_id"):
                    query = query.where("product_id", "==", filters["product_id"])
                if filters.get("platform"):
                    query = query.where("platform", "==", filters["platform"])
                if filters.get("currency"):
                    query = query.where("currency", "==", filters["currency"])
                if filters.get("is_sale") is not None:
                    query = query.where("is_sale", "==", filters["is_sale"])
                if filters.get("is_available") is not None:
                    query = query.where("is_available", "==", filters["is_available"])

            docs = list(query.order_by("created_at", direction=firestore.Query.DESCENDING).stream())
            prices = [doc.to_dict() for doc in docs]
            return prices[skip : skip + limit]
        except Exception as e:
            logger.error(f"Failed to list prices: {e}")
            raise

    # -----------------------------
    # Get Single Price
    # -----------------------------
    async def get_price(self, price_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a price by ID (Firestore)
        """
        try:
            doc = self.prices_ref.document(price_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Failed to get price {price_id}: {e}")
            raise

    # -----------------------------
    # Product Price History
    # -----------------------------
    async def get_product_price_history(
        self, product_id: str, days: int = 30, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Get price history for a product (Firestore)
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            query = (
                self.prices_ref.where("product_id", "==", product_id)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            docs = list(query.stream())
            prices = []
            for doc in docs:
                data = doc.to_dict()
                created_at = data.get("created_at")
                if created_at and isinstance(created_at, datetime):
                    if start_date <= created_at <= end_date:
                        prices.append(data)

            stats = await self._calculate_price_stats(prices)
            return prices, stats
        except Exception as e:
            logger.error(f"Failed to get price history for {product_id}: {e}")
            raise

    async def get_product_price_stats(self, product_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get summary price stats for a product
        """
        try:
            prices, stats = await self.get_product_price_history(product_id, days)
            product_doc = self.products_ref.document(product_id).get()
            if product_doc.exists:
                product = product_doc.to_dict()
                stats.update(
                    {
                        "product_id": product_id,
                        "current_price": product.get("current_price"),
                        "original_price": product.get("original_price"),
                        "is_on_sale": product.get("is_on_sale", False),
                    }
                )
            return stats
        except Exception as e:
            logger.error(f"Failed to get product price stats: {e}")
            raise

    # -----------------------------
    # Internal Stats Helper
    # -----------------------------
    async def _calculate_price_stats(self, prices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate min, max, avg, trend, etc.
        """
        try:
            if not prices:
                return {
                    "total_prices": 0,
                    "min_price": None,
                    "max_price": None,
                    "avg_price": None,
                    "price_trend": "unknown",
                    "price_change_percentage": 0.0,
                }

            values = [p["price"] for p in prices if p.get("price")]
            if not values:
                return {
                    "total_prices": len(prices),
                    "min_price": None,
                    "max_price": None,
                    "avg_price": None,
                    "price_trend": "unknown",
                    "price_change_percentage": 0.0,
                }

            min_p, max_p, avg_p = min(values), max(values), sum(values) / len(values)
            first, last = values[-1], values[0]
            trend = (
                "increasing"
                if last > first * 1.05
                else "decreasing"
                if last < first * 0.95
                else "stable"
            )
            pct = ((last - first) / first) * 100 if first else 0.0
            return {
                "total_prices": len(prices),
                "min_price": min_p,
                "max_price": max_p,
                "avg_price": round(avg_p, 2),
                "price_trend": trend,
                "price_change_percentage": round(pct, 2),
            }
        except Exception as e:
            logger.error(f"Failed to calculate Firestore price stats: {e}")
            return {}

    # -----------------------------
    # Popular Price Trends
    # -----------------------------
    async def get_popular_price_trends(
        self,
        platform: Optional[str] = None,
        category: Optional[str] = None,
        days: int = 7,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get products with frequent price updates or popular trends
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            products = [doc.to_dict() for doc in self.products_ref.stream()]
            prices = [doc.to_dict() for doc in self.prices_ref.stream()]

            result = []
            for p in products:
                if platform and p.get("platform") != platform:
                    continue
                if category and p.get("category") != category:
                    continue
                related_prices = [
                    pr
                    for pr in prices
                    if pr.get("product_id") == p["id"]
                    and pr.get("created_at")
                    and start_date <= pr["created_at"] <= end_date
                ]
                if not related_prices:
                    continue
                stats = await self._calculate_price_stats(related_prices)
                result.append(
                    {
                        "product_id": p["id"],
                        "product_name": p["name"],
                        "platform": p.get("platform"),
                        "category": p.get("category"),
                        "current_price": p.get("current_price"),
                        "price_count": len(related_prices),
                        **stats,
                    }
                )
            result.sort(key=lambda x: x["price_count"], reverse=True)
            return result[:limit]
        except Exception as e:
            logger.error(f"Failed to get popular trends: {e}")
            raise

    # -----------------------------
    # Price Drops & Increases
    # -----------------------------
    async def get_price_drops(
        self, threshold_percentage: float = 5.0, days: int = 7, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get products with significant price drops
        """
        try:
            products = [doc.to_dict() for doc in self.products_ref.stream()]
            result = []
            for p in products:
                cp, op = p.get("current_price"), p.get("original_price")
                if not cp or not op or cp >= op:
                    continue
                pct = ((op - cp) / op) * 100
                if pct >= threshold_percentage:
                    result.append(
                        {
                            "product_id": p["id"],
                            "product_name": p["name"],
                            "platform": p.get("platform"),
                            "current_price": cp,
                            "original_price": op,
                            "savings_amount": round(op - cp, 2),
                            "savings_percentage": round(pct, 2),
                        }
                    )
            result.sort(key=lambda x: x["savings_percentage"], reverse=True)
            return result[:limit]
        except Exception as e:
            logger.error(f"Failed to get price drops: {e}")
            raise

    async def get_price_increases(
        self, threshold_percentage: float = 5.0, days: int = 7, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get products with significant price increases
        """
        try:
            products = [doc.to_dict() for doc in self.products_ref.stream()]
            result = []
            for p in products:
                cp, op = p.get("current_price"), p.get("original_price")
                if not cp or not op or cp <= op:
                    continue
                pct = ((cp - op) / op) * 100
                if pct >= threshold_percentage:
                    result.append(
                        {
                            "product_id": p["id"],
                            "product_name": p["name"],
                            "platform": p.get("platform"),
                            "current_price": cp,
                            "original_price": op,
                            "increase_amount": round(cp - op, 2),
                            "increase_percentage": round(pct, 2),
                        }
                    )
            result.sort(key=lambda x: x["increase_percentage"], reverse=True)
            return result[:limit]
        except Exception as e:
            logger.error(f"Failed to get price increases: {e}")
            raise

    # -----------------------------
    # Cleanup Old Prices
    # -----------------------------
    async def cleanup_old_prices(self, days_to_keep: int = 90) -> int:
        """
        Delete old price records from Firestore
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
            deleted = 0
            for doc in self.prices_ref.stream():
                data = doc.to_dict()
                if data.get("created_at") and data["created_at"] < cutoff:
                    self.prices_ref.document(doc.id).delete()
                    deleted += 1
            logger.info(f"Deleted {deleted} old price records")
            return deleted
        except Exception as e:
            logger.error(f"Failed to clean old prices: {e}")
            raise
