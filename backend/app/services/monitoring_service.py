"""
Monitoring service for price tracking and analytics (Firebase Firestore version)
"""

from firebase_admin import firestore
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import statistics

logger = logging.getLogger(__name__)
db = firestore.client()


class MonitoringService:
    """
    Firebase Firestore-based Monitoring & Analytics Service
    """

    def __init__(self):
        self.products_ref = db.collection("products")
        self.prices_ref = db.collection("prices")
        self.alerts_ref = db.collection("alerts")
        self.users_ref = db.collection("users")

    # -----------------------------
    # Product Price History
    # -----------------------------
    async def get_product_price_history(
        self, product_id: str, days: int = 30, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Get price history for a product (from Firestore)
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            query = (
                self.prices_ref.where("product_id", "==", product_id)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            docs = query.stream()
            history = []
            for doc in docs:
                data = doc.to_dict()
                created_at = data.get("created_at")
                if created_at and isinstance(created_at, datetime):
                    if start_date <= created_at <= end_date:
                        history.append(data)

            stats = await self._calculate_history_stats(history)
            return history, stats

        except Exception as e:
            logger.error(f"Failed to get Firestore price history: {e}")
            raise

    async def _calculate_history_stats(
        self, history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate price statistics from Firestore price history
        """
        if not history:
            return {
                "total_records": 0,
                "min_price": None,
                "max_price": None,
                "avg_price": None,
                "price_trend": "unknown",
                "volatility": 0.0,
            }

        prices = [h["price"] for h in history if "price" in h and h["price"]]
        if not prices:
            return {
                "total_records": len(history),
                "min_price": None,
                "max_price": None,
                "avg_price": None,
                "price_trend": "unknown",
                "volatility": 0.0,
            }

        min_p, max_p, avg_p = min(prices), max(prices), sum(prices) / len(prices)
        first_p, last_p = prices[-1], prices[0]
        trend = (
            "increasing"
            if last_p > first_p * 1.05
            else "decreasing"
            if last_p < first_p * 0.95
            else "stable"
        )
        volatility = statistics.pstdev(prices) if len(prices) > 1 else 0.0

        return {
            "total_records": len(history),
            "min_price": min_p,
            "max_price": max_p,
            "avg_price": round(avg_p, 2),
            "price_trend": trend,
            "volatility": round(volatility, 2),
        }

    # -----------------------------
    # User Monitoring Statistics
    # -----------------------------
    async def get_user_monitoring_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get monitoring summary for a Firebase user
        """
        try:
            # Alerts
            alerts = [
                doc.to_dict()
                for doc in self.alerts_ref.where("user_id", "==", user_id).stream()
            ]
            total_alerts = len(alerts)
            active_alerts = len([a for a in alerts if a.get("is_active")])
            triggered_alerts = len([a for a in alerts if a.get("is_triggered")])

            # Products being tracked
            tracked = [
                doc.to_dict()
                for doc in self.products_ref.where("is_tracking", "==", True).stream()
            ]
            tracked_products = len(tracked)

            # Recent price changes (last 7 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            prices = [
                doc.to_dict()
                for doc in self.prices_ref.stream()
                if doc.to_dict().get("created_at")
                and doc.to_dict()["created_at"] >= recent_cutoff
            ]
            recent_changes = len(prices)

            # Alerts by type
            alert_type_counts: Dict[str, int] = {}
            for a in alerts:
                t = a.get("alert_type", "unknown")
                alert_type_counts[t] = alert_type_counts.get(t, 0) + 1

            return {
                "total_alerts": total_alerts,
                "active_alerts": active_alerts,
                "triggered_alerts": triggered_alerts,
                "tracked_products": tracked_products,
                "recent_price_changes": recent_changes,
                "alert_types": alert_type_counts,
            }

        except Exception as e:
            logger.error(f"Failed to get monitoring stats for user {user_id}: {e}")
            return {}

    # -----------------------------
    # Price Change Trends
    # -----------------------------
    async def get_price_change_trends(
        self, days: int = 7, threshold_percentage: float = 5.0, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get products with significant price changes in last N days
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            products = [doc.to_dict() for doc in self.products_ref.stream()]
            trends = []
            for p in products:
                current = p.get("current_price")
                original = p.get("original_price") or current
                if not current or not original:
                    continue

                change = current - original
                pct = abs(change / original) * 100
                if pct >= threshold_percentage:
                    trends.append(
                        {
                            "product_id": p["id"],
                            "product_name": p["name"],
                            "platform": p.get("platform"),
                            "category": p.get("category"),
                            "current_price": current,
                            "original_price": original,
                            "change_amount": round(change, 2),
                            "change_percentage": round(pct, 2),
                            "trend": "increasing" if change > 0 else "decreasing",
                        }
                    )

            trends.sort(key=lambda x: x["change_percentage"], reverse=True)
            return trends[:limit]

        except Exception as e:
            logger.error(f"Failed to get Firestore price trends: {e}")
            return []

    # -----------------------------
    # Overview / Platform / Category Stats
    # -----------------------------
    async def get_monitoring_overview(self) -> Dict[str, Any]:
        """
        Get overall monitoring summary (Firestore version)
        """
        try:
            products = [doc.to_dict() for doc in self.products_ref.stream()]
            alerts = [doc.to_dict() for doc in self.alerts_ref.stream()]
            users = [doc.to_dict() for doc in self.users_ref.stream()]
            prices = [doc.to_dict() for doc in self.prices_ref.stream()]

            total_products = len(products)
            tracking_products = len([p for p in products if p.get("is_tracking")])
            total_alerts = len(alerts)
            active_alerts = len([a for a in alerts if a.get("is_active")])
            total_users = len(users)
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_price_changes = len(
                [
                    pr
                    for pr in prices
                    if pr.get("created_at")
                    and pr["created_at"] >= recent_cutoff
                ]
            )
            recent_alerts_triggered = len(
                [a for a in alerts if a.get("is_triggered")]
            )

            # Group by platform
            platforms: Dict[str, Dict[str, Any]] = {}
            for p in products:
                platform = p.get("platform", "unknown")
                price = p.get("current_price")
                if not price:
                    continue
                platforms.setdefault(platform, {"count": 0, "prices": []})
                platforms[platform]["count"] += 1
                platforms[platform]["prices"].append(price)

            platform_stats = {
                k: {
                    "product_count": v["count"],
                    "avg_price": round(sum(v["prices"]) / len(v["prices"]), 2)
                    if v["prices"]
                    else None,
                    "min_price": min(v["prices"]) if v["prices"] else None,
                    "max_price": max(v["prices"]) if v["prices"] else None,
                }
                for k, v in platforms.items()
            }

            # Group by category
            categories: Dict[str, Dict[str, Any]] = {}
            for p in products:
                cat = p.get("category", "Uncategorized")
                price = p.get("current_price")
                if not price:
                    continue
                categories.setdefault(cat, {"count": 0, "prices": []})
                categories[cat]["count"] += 1
                categories[cat]["prices"].append(price)

            category_stats = {
                k: {
                    "product_count": v["count"],
                    "avg_price": round(sum(v["prices"]) / len(v["prices"]), 2)
                    if v["prices"]
                    else None,
                    "min_price": min(v["prices"]) if v["prices"] else None,
                    "max_price": max(v["prices"]) if v["prices"] else None,
                }
                for k, v in categories.items()
            }

            return {
                "overview": {
                    "total_products": total_products,
                    "tracking_products": tracking_products,
                    "total_alerts": total_alerts,
                    "active_alerts": active_alerts,
                    "total_users": total_users,
                    "recent_price_changes": recent_price_changes,
                    "recent_alerts_triggered": recent_alerts_triggered,
                },
                "platforms": platform_stats,
                "categories": category_stats,
            }

        except Exception as e:
            logger.error(f"Failed to get Firestore monitoring overview: {e}")
            return {}
