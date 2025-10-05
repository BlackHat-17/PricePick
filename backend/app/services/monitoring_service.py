"""
Monitoring service for price tracking and analytics
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from app.models.monitoring import PriceAlert, PriceHistory
from app.models.product import Product
from app.models.price import Price
from app.models.user import User

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Service class for monitoring and analytics operations
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_product_price_history(
        self, 
        product_id: int, 
        days: int = 30, 
        limit: int = 100
    ) -> Tuple[List[PriceHistory], Dict[str, Any]]:
        """
        Get price history for a product
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get price history
            history = self.db.query(PriceHistory).filter(
                and_(
                    PriceHistory.product_id == product_id,
                    PriceHistory.created_at >= start_date,
                    PriceHistory.created_at <= end_date,
                    PriceHistory.is_active == True
                )
            ).order_by(desc(PriceHistory.created_at)).limit(limit).all()
            
            # Calculate statistics
            stats = await self._calculate_history_stats(history)
            
            return history, stats
            
        except Exception as e:
            logger.error(f"Failed to get price history for product {product_id}: {str(e)}")
            raise
    
    async def _calculate_history_stats(self, history: List[PriceHistory]) -> Dict[str, Any]:
        """
        Calculate statistics from price history
        """
        try:
            if not history:
                return {
                    "total_records": 0,
                    "min_price": None,
                    "max_price": None,
                    "avg_price": None,
                    "price_trend": "unknown",
                    "volatility": 0.0
                }
            
            # Extract price values
            price_values = [h.price for h in history if h.price is not None]
            
            if not price_values:
                return {
                    "total_records": len(history),
                    "min_price": None,
                    "max_price": None,
                    "avg_price": None,
                    "price_trend": "unknown",
                    "volatility": 0.0
                }
            
            # Calculate basic statistics
            min_price = min(price_values)
            max_price = max(price_values)
            avg_price = sum(price_values) / len(price_values)
            
            # Calculate trend
            if len(price_values) >= 2:
                first_price = price_values[-1]  # Oldest price
                last_price = price_values[0]   # Newest price
                
                if last_price > first_price * 1.05:  # 5% increase
                    trend = "increasing"
                elif last_price < first_price * 0.95:  # 5% decrease
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "unknown"
            
            # Calculate volatility (standard deviation)
            if len(price_values) > 1:
                variance = sum((x - avg_price) ** 2 for x in price_values) / len(price_values)
                volatility = variance ** 0.5
            else:
                volatility = 0.0
            
            return {
                "total_records": len(history),
                "min_price": min_price,
                "max_price": max_price,
                "avg_price": round(avg_price, 2),
                "price_trend": trend,
                "volatility": round(volatility, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate history stats: {str(e)}")
            return {}
    
    async def get_user_monitoring_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get monitoring statistics for a user
        """
        try:
            # Count user's alerts
            total_alerts = self.db.query(PriceAlert).filter(
                PriceAlert.user_id == user_id
            ).count()
            
            active_alerts = self.db.query(PriceAlert).filter(
                and_(
                    PriceAlert.user_id == user_id,
                    PriceAlert.is_active == True
                )
            ).count()
            
            triggered_alerts = self.db.query(PriceAlert).filter(
                and_(
                    PriceAlert.user_id == user_id,
                    PriceAlert.is_triggered == True
                )
            ).count()
            
            # Count user's products being tracked
            tracked_products = self.db.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.is_tracking == True,
                    Product.id.in_(
                        self.db.query(PriceAlert.product_id).filter(
                            PriceAlert.user_id == user_id
                        )
                    )
                )
            ).count()
            
            # Count recent price changes for user's products
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_changes = self.db.query(Price).filter(
                and_(
                    Price.product_id.in_(
                        self.db.query(PriceAlert.product_id).filter(
                            PriceAlert.user_id == user_id
                        )
                    ),
                    Price.created_at >= recent_cutoff
                )
            ).count()
            
            # Count alerts by type
            alert_types = self.db.query(
                PriceAlert.alert_type,
                func.count(PriceAlert.id).label('count')
            ).filter(
                and_(
                    PriceAlert.user_id == user_id,
                    PriceAlert.is_active == True
                )
            ).group_by(PriceAlert.alert_type).all()
            
            alert_type_counts = {alert_type: count for alert_type, count in alert_types}
            
            return {
                "total_alerts": total_alerts,
                "active_alerts": active_alerts,
                "triggered_alerts": triggered_alerts,
                "tracked_products": tracked_products,
                "recent_price_changes": recent_changes,
                "alert_types": alert_type_counts
            }
            
        except Exception as e:
            logger.error(f"Failed to get monitoring stats for user {user_id}: {str(e)}")
            return {}
    
    async def get_price_change_trends(
        self, 
        days: int = 7,
        threshold_percentage: float = 5.0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get price change trends across all products
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get products with significant price changes
            query = self.db.query(
                Product.id,
                Product.name,
                Product.platform,
                Product.category,
                Product.current_price,
                Product.original_price,
                func.count(Price.id).label('price_count'),
                func.avg(Price.price).label('avg_price')
            ).join(Price, Product.id == Price.product_id).filter(
                and_(
                    Price.created_at >= start_date,
                    Price.created_at <= end_date,
                    Price.is_active == True,
                    Product.is_active == True,
                    Product.current_price.isnot(None),
                    Product.original_price.isnot(None)
                )
            ).group_by(
                Product.id, Product.name, Product.platform, 
                Product.category, Product.current_price, Product.original_price
            ).having(
                func.abs(Product.current_price - Product.original_price) / Product.original_price * 100 >= threshold_percentage
            ).order_by(
                desc(func.abs(Product.current_price - Product.original_price) / Product.original_price * 100)
            ).limit(limit)
            
            results = query.all()
            
            # Format results
            trends = []
            for result in results:
                change_amount = result.current_price - result.original_price
                change_percentage = (change_amount / result.original_price) * 100
                
                trends.append({
                    "product_id": result.id,
                    "product_name": result.name,
                    "platform": result.platform,
                    "category": result.category,
                    "current_price": result.current_price,
                    "original_price": result.original_price,
                    "change_amount": round(change_amount, 2),
                    "change_percentage": round(change_percentage, 2),
                    "price_count": result.price_count,
                    "avg_price": round(result.avg_price, 2) if result.avg_price else None,
                    "trend": "increasing" if change_amount > 0 else "decreasing"
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get price change trends: {str(e)}")
            raise
    
    async def get_platform_statistics(self) -> Dict[str, Any]:
        """
        Get statistics by platform
        """
        try:
            # Count products by platform
            platform_counts = self.db.query(
                Product.platform,
                func.count(Product.id).label('product_count'),
                func.avg(Product.current_price).label('avg_price'),
                func.min(Product.current_price).label('min_price'),
                func.max(Product.current_price).label('max_price')
            ).filter(
                Product.is_active == True
            ).group_by(Product.platform).all()
            
            # Count price changes by platform
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            platform_changes = self.db.query(
                Product.platform,
                func.count(Price.id).label('change_count')
            ).join(Price, Product.id == Price.product_id).filter(
                and_(
                    Price.created_at >= recent_cutoff,
                    Price.is_active == True,
                    Product.is_active == True
                )
            ).group_by(Product.platform).all()
            
            # Format results
            platforms = {}
            for platform, product_count, avg_price, min_price, max_price in platform_counts:
                platforms[platform] = {
                    "product_count": product_count,
                    "avg_price": round(avg_price, 2) if avg_price else None,
                    "min_price": min_price,
                    "max_price": max_price,
                    "recent_changes": 0
                }
            
            # Add change counts
            for platform, change_count in platform_changes:
                if platform in platforms:
                    platforms[platform]["recent_changes"] = change_count
            
            return platforms
            
        except Exception as e:
            logger.error(f"Failed to get platform statistics: {str(e)}")
            return {}
    
    async def get_category_statistics(self) -> Dict[str, Any]:
        """
        Get statistics by category
        """
        try:
            # Count products by category
            category_counts = self.db.query(
                Product.category,
                func.count(Product.id).label('product_count'),
                func.avg(Product.current_price).label('avg_price'),
                func.min(Product.current_price).label('min_price'),
                func.max(Product.current_price).label('max_price')
            ).filter(
                and_(
                    Product.is_active == True,
                    Product.category.isnot(None)
                )
            ).group_by(Product.category).all()
            
            # Count price changes by category
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            category_changes = self.db.query(
                Product.category,
                func.count(Price.id).label('change_count')
            ).join(Price, Product.id == Price.product_id).filter(
                and_(
                    Price.created_at >= recent_cutoff,
                    Price.is_active == True,
                    Product.is_active == True,
                    Product.category.isnot(None)
                )
            ).group_by(Product.category).all()
            
            # Format results
            categories = {}
            for category, product_count, avg_price, min_price, max_price in category_counts:
                categories[category] = {
                    "product_count": product_count,
                    "avg_price": round(avg_price, 2) if avg_price else None,
                    "min_price": min_price,
                    "max_price": max_price,
                    "recent_changes": 0
                }
            
            # Add change counts
            for category, change_count in category_changes:
                if category in categories:
                    categories[category]["recent_changes"] = change_count
            
            return categories
            
        except Exception as e:
            logger.error(f"Failed to get category statistics: {str(e)}")
            return {}
    
    async def get_monitoring_overview(self) -> Dict[str, Any]:
        """
        Get overall monitoring statistics
        """
        try:
            # Total counts
            total_products = self.db.query(Product).filter(Product.is_active == True).count()
            tracking_products = self.db.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.is_tracking == True
                )
            ).count()
            
            total_alerts = self.db.query(PriceAlert).count()
            active_alerts = self.db.query(PriceAlert).filter(
                PriceAlert.is_active == True
            ).count()
            
            total_users = self.db.query(User).filter(User.is_active == True).count()
            
            # Recent activity
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_price_changes = self.db.query(Price).filter(
                and_(
                    Price.created_at >= recent_cutoff,
                    Price.is_active == True
                )
            ).count()
            
            recent_alerts_triggered = self.db.query(PriceAlert).filter(
                and_(
                    PriceAlert.triggered_at.like(f"{datetime.utcnow().date()}%"),
                    PriceAlert.is_triggered == True
                )
            ).count()
            
            # Platform distribution
            platform_stats = await self.get_platform_statistics()
            
            # Category distribution
            category_stats = await self.get_category_statistics()
            
            return {
                "overview": {
                    "total_products": total_products,
                    "tracking_products": tracking_products,
                    "total_alerts": total_alerts,
                    "active_alerts": active_alerts,
                    "total_users": total_users,
                    "recent_price_changes": recent_price_changes,
                    "recent_alerts_triggered": recent_alerts_triggered
                },
                "platforms": platform_stats,
                "categories": category_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get monitoring overview: {str(e)}")
            return {}
