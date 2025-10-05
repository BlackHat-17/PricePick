"""
Price service for managing price data and statistics
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from app.models.price import Price
from app.models.product import Product
from app.models.monitoring import PriceHistory

logger = logging.getLogger(__name__)


class PriceService:
    """
    Service class for price-related operations
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def list_prices(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Price]:
        """
        List prices with filtering and pagination
        """
        try:
            query = self.db.query(Price).filter(Price.is_active == True)
            
            # Apply filters
            if filters:
                if filters.get("product_id"):
                    query = query.filter(Price.product_id == filters["product_id"])
                
                if filters.get("platform"):
                    query = query.join(Product).filter(Product.platform == filters["platform"])
                
                if filters.get("currency"):
                    query = query.filter(Price.currency == filters["currency"])
                
                if filters.get("is_sale") is not None:
                    query = query.filter(Price.is_sale == filters["is_sale"])
                
                if filters.get("is_available") is not None:
                    query = query.filter(Price.is_available == filters["is_available"])
                
                if filters.get("start_date"):
                    query = query.filter(Price.created_at >= filters["start_date"])
                
                if filters.get("end_date"):
                    query = query.filter(Price.created_at <= filters["end_date"])
            
            return query.order_by(desc(Price.created_at)).offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to list prices: {str(e)}")
            raise
    
    async def get_price(self, price_id: int) -> Optional[Price]:
        """
        Get a price by ID
        """
        try:
            return self.db.query(Price).filter(
                and_(Price.id == price_id, Price.is_active == True)
            ).first()
        except Exception as e:
            logger.error(f"Failed to get price {price_id}: {str(e)}")
            raise
    
    async def get_product_price_history(
        self, 
        product_id: int, 
        days: int = 30, 
        limit: int = 100
    ) -> Tuple[List[Price], Dict[str, Any]]:
        """
        Get price history for a product with statistics
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get prices
            prices = self.db.query(Price).filter(
                and_(
                    Price.product_id == product_id,
                    Price.created_at >= start_date,
                    Price.created_at <= end_date,
                    Price.is_active == True
                )
            ).order_by(desc(Price.created_at)).limit(limit).all()
            
            # Calculate statistics
            stats = await self._calculate_price_stats(prices)
            
            return prices, stats
            
        except Exception as e:
            logger.error(f"Failed to get price history for product {product_id}: {str(e)}")
            raise
    
    async def get_product_price_stats(self, product_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get price statistics for a product
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get prices
            prices = self.db.query(Price).filter(
                and_(
                    Price.product_id == product_id,
                    Price.created_at >= start_date,
                    Price.created_at <= end_date,
                    Price.is_active == True
                )
            ).all()
            
            if not prices:
                return {
                    "product_id": product_id,
                    "total_prices": 0,
                    "current_price": None,
                    "min_price": None,
                    "max_price": None,
                    "avg_price": None,
                    "price_trend": "unknown",
                    "price_change_percentage": 0.0
                }
            
            # Calculate statistics
            stats = await self._calculate_price_stats(prices)
            
            # Add product-specific info
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if product:
                stats["current_price"] = product.current_price
                stats["original_price"] = product.original_price
                stats["is_on_sale"] = product.is_on_sale
                stats["price_change_percentage"] = product.price_change_percentage
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get price stats for product {product_id}: {str(e)}")
            raise
    
    async def _calculate_price_stats(self, prices: List[Price]) -> Dict[str, Any]:
        """
        Calculate price statistics from a list of prices
        """
        try:
            if not prices:
                return {
                    "total_prices": 0,
                    "min_price": None,
                    "max_price": None,
                    "avg_price": None,
                    "price_trend": "unknown",
                    "price_change_percentage": 0.0
                }
            
            # Extract price values
            price_values = [p.price for p in prices if p.price is not None]
            
            if not price_values:
                return {
                    "total_prices": len(prices),
                    "min_price": None,
                    "max_price": None,
                    "avg_price": None,
                    "price_trend": "unknown",
                    "price_change_percentage": 0.0
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
                
                price_change_percentage = ((last_price - first_price) / first_price) * 100
            else:
                trend = "unknown"
                price_change_percentage = 0.0
            
            return {
                "total_prices": len(prices),
                "min_price": min_price,
                "max_price": max_price,
                "avg_price": round(avg_price, 2),
                "price_trend": trend,
                "price_change_percentage": round(price_change_percentage, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate price stats: {str(e)}")
            return {}
    
    async def get_popular_price_trends(
        self, 
        platform: Optional[str] = None,
        category: Optional[str] = None,
        days: int = 7,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get popular price trends across products
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Build query
            query = self.db.query(
                Product.id,
                Product.name,
                Product.platform,
                Product.category,
                Product.current_price,
                func.count(Price.id).label('price_count'),
                func.avg(Price.price).label('avg_price'),
                func.min(Price.price).label('min_price'),
                func.max(Price.price).label('max_price')
            ).join(Price, Product.id == Price.product_id).filter(
                and_(
                    Price.created_at >= start_date,
                    Price.created_at <= end_date,
                    Price.is_active == True,
                    Product.is_active == True
                )
            )
            
            # Apply filters
            if platform:
                query = query.filter(Product.platform == platform)
            
            if category:
                query = query.filter(Product.category == category)
            
            # Group by product and order by price count
            results = query.group_by(
                Product.id, Product.name, Product.platform, 
                Product.category, Product.current_price
            ).order_by(desc('price_count')).limit(limit).all()
            
            # Format results
            trends = []
            for result in results:
                trends.append({
                    "product_id": result.id,
                    "product_name": result.name,
                    "platform": result.platform,
                    "category": result.category,
                    "current_price": result.current_price,
                    "price_count": result.price_count,
                    "avg_price": round(result.avg_price, 2) if result.avg_price else None,
                    "min_price": result.min_price,
                    "max_price": result.max_price
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get popular price trends: {str(e)}")
            raise
    
    async def get_price_drops(
        self, 
        threshold_percentage: float = 5.0,
        days: int = 7,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get products with significant price drops
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get products with price drops
            query = self.db.query(
                Product.id,
                Product.name,
                Product.platform,
                Product.current_price,
                Product.original_price,
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
                Product.current_price, Product.original_price
            ).having(
                (Product.current_price < Product.original_price) &
                ((Product.original_price - Product.current_price) / Product.original_price * 100 >= threshold_percentage)
            ).order_by(
                desc((Product.original_price - Product.current_price) / Product.original_price * 100)
            ).limit(limit)
            
            results = query.all()
            
            # Format results
            price_drops = []
            for result in results:
                savings_amount = result.original_price - result.current_price
                savings_percentage = (savings_amount / result.original_price) * 100
                
                price_drops.append({
                    "product_id": result.id,
                    "product_name": result.name,
                    "platform": result.platform,
                    "current_price": result.current_price,
                    "original_price": result.original_price,
                    "savings_amount": round(savings_amount, 2),
                    "savings_percentage": round(savings_percentage, 2),
                    "avg_price": round(result.avg_price, 2) if result.avg_price else None
                })
            
            return price_drops
            
        except Exception as e:
            logger.error(f"Failed to get price drops: {str(e)}")
            raise
    
    async def get_price_increases(
        self, 
        threshold_percentage: float = 5.0,
        days: int = 7,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get products with significant price increases
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get products with price increases
            query = self.db.query(
                Product.id,
                Product.name,
                Product.platform,
                Product.current_price,
                Product.original_price,
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
                Product.current_price, Product.original_price
            ).having(
                (Product.current_price > Product.original_price) &
                ((Product.current_price - Product.original_price) / Product.original_price * 100 >= threshold_percentage)
            ).order_by(
                desc((Product.current_price - Product.original_price) / Product.original_price * 100)
            ).limit(limit)
            
            results = query.all()
            
            # Format results
            price_increases = []
            for result in results:
                increase_amount = result.current_price - result.original_price
                increase_percentage = (increase_amount / result.original_price) * 100
                
                price_increases.append({
                    "product_id": result.id,
                    "product_name": result.name,
                    "platform": result.platform,
                    "current_price": result.current_price,
                    "original_price": result.original_price,
                    "increase_amount": round(increase_amount, 2),
                    "increase_percentage": round(increase_percentage, 2),
                    "avg_price": round(result.avg_price, 2) if result.avg_price else None
                })
            
            return price_increases
            
        except Exception as e:
            logger.error(f"Failed to get price increases: {str(e)}")
            raise
    
    async def compare_product_prices(
        self, 
        product_id1: int, 
        product_id2: int, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Compare prices between two products
        """
        try:
            # Get both products
            product1 = self.db.query(Product).filter(Product.id == product_id1).first()
            product2 = self.db.query(Product).filter(Product.id == product_id2).first()
            
            if not product1 or not product2:
                return {"error": "One or both products not found"}
            
            # Get price history for both products
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            prices1 = self.db.query(Price).filter(
                and_(
                    Price.product_id == product_id1,
                    Price.created_at >= start_date,
                    Price.created_at <= end_date,
                    Price.is_active == True
                )
            ).all()
            
            prices2 = self.db.query(Price).filter(
                and_(
                    Price.product_id == product_id2,
                    Price.created_at >= start_date,
                    Price.created_at <= end_date,
                    Price.is_active == True
                )
            ).all()
            
            # Calculate statistics for both products
            stats1 = await self._calculate_price_stats(prices1)
            stats2 = await self._calculate_price_stats(prices2)
            
            # Calculate comparison metrics
            comparison = {
                "product1": {
                    "id": product1.id,
                    "name": product1.name,
                    "platform": product1.platform,
                    "current_price": product1.current_price,
                    "stats": stats1
                },
                "product2": {
                    "id": product2.id,
                    "name": product2.name,
                    "platform": product2.platform,
                    "current_price": product2.current_price,
                    "stats": stats2
                },
                "comparison": {
                    "price_difference": None,
                    "price_difference_percentage": None,
                    "cheaper_product": None,
                    "better_value": None
                }
            }
            
            # Calculate price difference
            if product1.current_price and product2.current_price:
                price_diff = product1.current_price - product2.current_price
                comparison["comparison"]["price_difference"] = round(price_diff, 2)
                
                if product2.current_price > 0:
                    price_diff_percentage = (price_diff / product2.current_price) * 100
                    comparison["comparison"]["price_difference_percentage"] = round(price_diff_percentage, 2)
                
                comparison["comparison"]["cheaper_product"] = product1.id if price_diff < 0 else product2.id
                
                # Determine better value (considering price and rating)
                if product1.rating and product2.rating:
                    value1 = product1.rating / product1.current_price if product1.current_price > 0 else 0
                    value2 = product2.rating / product2.current_price if product2.current_price > 0 else 0
                    comparison["comparison"]["better_value"] = product1.id if value1 > value2 else product2.id
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare products {product_id1} and {product_id2}: {str(e)}")
            raise
    
    async def cleanup_old_prices(self, cutoff_date: datetime) -> int:
        """
        Clean up old price data
        """
        try:
            # Count old prices
            old_prices_count = self.db.query(Price).filter(
                Price.created_at < cutoff_date
            ).count()
            
            # Delete old prices
            self.db.query(Price).filter(
                Price.created_at < cutoff_date
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Cleaned up {old_prices_count} old price records")
            return old_prices_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cleanup old prices: {str(e)}")
            raise
