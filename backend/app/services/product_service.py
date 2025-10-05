"""
Product service for managing product data and operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

from app.models.product import Product
from app.models.price import Price
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.scraping_service import ScrapingService

logger = logging.getLogger(__name__)


class ProductService:
    """
    Service class for product-related operations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.scraping_service = ScrapingService(db)
    
    async def create_product(self, product_data: ProductCreate) -> Product:
        """
        Create a new product
        """
        try:
            # Create product instance
            product = Product(
                name=product_data.name,
                description=product_data.description,
                brand=product_data.brand,
                category=product_data.category,
                sku=product_data.sku,
                upc=product_data.upc,
                asin=product_data.asin,
                platform=product_data.platform,
                platform_product_id=product_data.platform_product_id,
                product_url=product_data.product_url,
                currency=product_data.currency,
                image_url=product_data.image_url,
                rating=product_data.rating,
                review_count=product_data.review_count,
                price_selector=product_data.price_selector,
                title_selector=product_data.title_selector,
                availability_selector=product_data.availability_selector,
                metadata=product_data.metadata
            )
            
            # Add to database
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            
            # Perform initial scraping to get current price
            try:
                await self.scraping_service.scrape_product(product, force=True)
            except Exception as e:
                logger.warning(f"Initial scraping failed for product {product.id}: {str(e)}")
            
            return product
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create product: {str(e)}")
            raise
    
    async def get_product(self, product_id: int) -> Optional[Product]:
        """
        Get a product by ID
        """
        try:
            return self.db.query(Product).filter(
                and_(Product.id == product_id, Product.is_active == True)
            ).first()
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {str(e)}")
            raise
    
    async def list_products(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Product], int]:
        """
        List products with filtering and pagination
        """
        try:
            query = self.db.query(Product).filter(Product.is_active == True)
            
            # Apply filters
            if filters:
                if filters.get("platform"):
                    query = query.filter(Product.platform == filters["platform"])
                
                if filters.get("category"):
                    query = query.filter(Product.category == filters["category"])
                
                if filters.get("brand"):
                    query = query.filter(Product.brand == filters["brand"])
                
                if filters.get("is_tracking") is not None:
                    query = query.filter(Product.is_tracking == filters["is_tracking"])
                
                if filters.get("search"):
                    search_term = f"%{filters['search']}%"
                    query = query.filter(
                        or_(
                            Product.name.ilike(search_term),
                            Product.description.ilike(search_term)
                        )
                    )
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            products = query.order_by(desc(Product.created_at)).offset(skip).limit(limit).all()
            
            return products, total
            
        except Exception as e:
            logger.error(f"Failed to list products: {str(e)}")
            raise
    
    async def update_product(self, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        """
        Update a product
        """
        try:
            product = await self.get_product(product_id)
            if not product:
                return None
            
            # Update fields
            update_data = product_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(product, field):
                    setattr(product, field, value)
            
            self.db.commit()
            self.db.refresh(product)
            
            return product
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update product {product_id}: {str(e)}")
            raise
    
    async def delete_product(self, product_id: int) -> bool:
        """
        Soft delete a product
        """
        try:
            product = await self.get_product(product_id)
            if not product:
                return False
            
            product.is_active = False
            product.is_tracking = False
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete product {product_id}: {str(e)}")
            raise
    
    async def get_price_history(
        self, 
        product_id: int, 
        days: int = 30, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get price history for a product
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
            
            # Convert to dictionary format
            price_history = []
            for price in prices:
                price_history.append({
                    "id": price.id,
                    "price": price.price,
                    "currency": price.currency,
                    "original_price": price.original_price,
                    "sale_price": price.sale_price,
                    "shipping_cost": price.shipping_cost,
                    "total_cost": price.effective_price,
                    "is_sale": price.is_sale,
                    "is_available": price.is_available,
                    "seller": price.seller,
                    "condition": price.condition,
                    "created_at": price.created_at.isoformat(),
                    "savings_amount": price.savings_amount,
                    "savings_percentage": price.savings_percentage
                })
            
            return price_history
            
        except Exception as e:
            logger.error(f"Failed to get price history for product {product_id}: {str(e)}")
            raise
    
    async def get_last_scraped_time(self, product_id: int) -> Optional[datetime]:
        """
        Get the last time a product was scraped
        """
        try:
            from app.models.scraping import ScrapingSession
            
            session = self.db.query(ScrapingSession).filter(
                and_(
                    ScrapingSession.product_id == product_id,
                    ScrapingSession.is_active == True
                )
            ).order_by(desc(ScrapingSession.created_at)).first()
            
            if session and session.completed_at:
                return datetime.fromisoformat(session.completed_at.replace('Z', '+00:00'))
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get last scraped time for product {product_id}: {str(e)}")
            return None
    
    async def update_tracking_status(self, product_id: int, is_tracking: bool) -> bool:
        """
        Update product tracking status
        """
        try:
            product = await self.get_product(product_id)
            if not product:
                return False
            
            product.is_tracking = is_tracking
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update tracking status for product {product_id}: {str(e)}")
            raise
    
    async def get_products_for_scraping(self, limit: int = 100) -> List[Product]:
        """
        Get products that need to be scraped
        """
        try:
            # Get products that are tracking and haven't been scraped recently
            cutoff_time = datetime.utcnow() - timedelta(hours=1)  # 1 hour ago
            
            products = self.db.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.is_tracking == True,
                    or_(
                        Product.updated_at < cutoff_time,
                        Product.updated_at.is_(None)
                    )
                )
            ).limit(limit).all()
            
            return products
            
        except Exception as e:
            logger.error(f"Failed to get products for scraping: {str(e)}")
            raise
    
    async def get_product_stats(self, product_id: int) -> Dict[str, Any]:
        """
        Get statistics for a product
        """
        try:
            product = await self.get_product(product_id)
            if not product:
                return {}
            
            # Get price statistics
            prices = self.db.query(Price).filter(
                and_(
                    Price.product_id == product_id,
                    Price.is_active == True
                )
            ).all()
            
            if not prices:
                return {
                    "product_id": product_id,
                    "total_prices": 0,
                    "current_price": product.current_price,
                    "price_trend": "unknown"
                }
            
            # Calculate statistics
            price_values = [p.price for p in prices if p.price]
            if price_values:
                min_price = min(price_values)
                max_price = max(price_values)
                avg_price = sum(price_values) / len(price_values)
                
                # Calculate trend
                recent_prices = sorted(price_values, reverse=True)[:5]
                if len(recent_prices) >= 2:
                    if recent_prices[0] > recent_prices[-1] * 1.05:
                        trend = "increasing"
                    elif recent_prices[0] < recent_prices[-1] * 0.95:
                        trend = "decreasing"
                    else:
                        trend = "stable"
                else:
                    trend = "unknown"
            else:
                min_price = max_price = avg_price = 0
                trend = "unknown"
            
            return {
                "product_id": product_id,
                "total_prices": len(prices),
                "current_price": product.current_price,
                "min_price": min_price,
                "max_price": max_price,
                "avg_price": avg_price,
                "price_trend": trend,
                "is_on_sale": product.is_on_sale,
                "price_change_percentage": product.price_change_percentage
            }
            
        except Exception as e:
            logger.error(f"Failed to get product stats for {product_id}: {str(e)}")
            raise
