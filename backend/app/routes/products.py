"""
Product management API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse
from app.services.product_service import ProductService
from app.services.scraping_service import ScrapingService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new product for price tracking
    """
    try:
        product_service = ProductService(db)
        product = await product_service.create_product(product_data)
        
        logger.info(f"Created product: {product.id} - {product.name}")
        return product
        
    except Exception as e:
        logger.error(f"Failed to create product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create product: {str(e)}"
        )


@router.get("/", response_model=ProductListResponse)
async def list_products(
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of products to return"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    is_tracking: Optional[bool] = Query(None, description="Filter by tracking status"),
    search: Optional[str] = Query(None, description="Search in product name and description"),
    db: Session = Depends(get_db)
):
    """
    List products with optional filtering and pagination
    """
    try:
        product_service = ProductService(db)
        
        filters = {
            "platform": platform,
            "category": category,
            "brand": brand,
            "is_tracking": is_tracking,
            "search": search
        }
        
        products, total = await product_service.list_products(
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        return ProductListResponse(
            products=products,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to list products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve products"
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific product by ID
    """
    try:
        product_service = ProductService(db)
        product = await product_service.get_product(product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product"
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a product
    """
    try:
        product_service = ProductService(db)
        product = await product_service.update_product(product_id, product_data)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        logger.info(f"Updated product: {product.id} - {product.name}")
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update product: {str(e)}"
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a product (soft delete)
    """
    try:
        product_service = ProductService(db)
        success = await product_service.delete_product(product_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        logger.info(f"Deleted product: {product_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )


@router.post("/{product_id}/scrape", response_model=dict)
async def scrape_product(
    product_id: int,
    force: bool = Query(False, description="Force scraping even if recently scraped"),
    db: Session = Depends(get_db)
):
    """
    Manually trigger product scraping
    """
    try:
        product_service = ProductService(db)
        scraping_service = ScrapingService(db)
        
        # Get product
        product = await product_service.get_product(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Check if scraping is needed
        if not force:
            last_scraped = await product_service.get_last_scraped_time(product_id)
            if last_scraped:
                time_diff = datetime.utcnow() - last_scraped
                if time_diff.total_seconds() < 300:  # 5 minutes
                    return {
                        "message": "Product was recently scraped",
                        "last_scraped": last_scraped.isoformat(),
                        "skipped": True
                    }
        
        # Perform scraping
        result = await scraping_service.scrape_product(product, force=force)
        
        logger.info(f"Scraped product {product_id}: {result['success']}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to scrape product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape product: {str(e)}"
        )


@router.get("/{product_id}/prices", response_model=List[dict])
async def get_product_prices(
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve prices for"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of prices to return"),
    db: Session = Depends(get_db)
):
    """
    Get price history for a product
    """
    try:
        product_service = ProductService(db)
        
        # Check if product exists
        product = await product_service.get_product(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Get price history
        prices = await product_service.get_price_history(product_id, days=days, limit=limit)
        
        return prices
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prices for product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price history"
        )


@router.post("/{product_id}/toggle-tracking", response_model=dict)
async def toggle_tracking(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Toggle product tracking on/off
    """
    try:
        product_service = ProductService(db)
        
        # Get product
        product = await product_service.get_product(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Toggle tracking
        new_status = not product.is_tracking
        await product_service.update_tracking_status(product_id, new_status)
        
        logger.info(f"Toggled tracking for product {product_id}: {new_status}")
        return {
            "product_id": product_id,
            "is_tracking": new_status,
            "message": f"Tracking {'enabled' if new_status else 'disabled'}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle tracking for product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle tracking"
        )


@router.get("/platforms/supported", response_model=List[dict])
async def get_supported_platforms():
    """
    Get list of supported e-commerce platforms
    """
    from config import SUPPORTED_PLATFORMS
    
    platforms = []
    for key, config in SUPPORTED_PLATFORMS.items():
        platforms.append({
            "key": key,
            "name": config["name"],
            "base_url": config["base_url"]
        })
    
    return platforms
