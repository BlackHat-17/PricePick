"""
Price tracking and history API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.price import Price
from app.schemas.price import PriceResponse, PriceHistoryResponse, PriceStatsResponse
from app.services.price_service import PriceService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[PriceResponse])
async def list_prices(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    currency: Optional[str] = Query(None, description="Filter by currency"),
    is_sale: Optional[bool] = Query(None, description="Filter by sale status"),
    is_available: Optional[bool] = Query(None, description="Filter by availability"),
    start_date: Optional[datetime] = Query(None, description="Start date for price range"),
    end_date: Optional[datetime] = Query(None, description="End date for price range"),
    skip: int = Query(0, ge=0, description="Number of prices to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of prices to return"),
    db: Session = Depends(get_db)
):
    """
    List prices with optional filtering and pagination
    """
    try:
        price_service = PriceService(db)
        
        filters = {
            "product_id": product_id,
            "platform": platform,
            "currency": currency,
            "is_sale": is_sale,
            "is_available": is_available,
            "start_date": start_date,
            "end_date": end_date
        }
        
        prices = await price_service.list_prices(
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        return prices
        
    except Exception as e:
        logger.error(f"Failed to list prices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prices"
        )


@router.get("/{price_id}", response_model=PriceResponse)
async def get_price(
    price_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific price by ID
    """
    try:
        price_service = PriceService(db)
        price = await price_service.get_price(price_id)
        
        if not price:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Price not found"
            )
        
        return price
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get price {price_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price"
        )


@router.get("/product/{product_id}/history", response_model=PriceHistoryResponse)
async def get_product_price_history(
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve prices for"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of prices to return"),
    db: Session = Depends(get_db)
):
    """
    Get price history for a specific product
    """
    try:
        price_service = PriceService(db)
        
        # Get price history
        prices, stats = await price_service.get_product_price_history(
            product_id=product_id,
            days=days,
            limit=limit
        )
        
        return PriceHistoryResponse(
            product_id=product_id,
            prices=prices,
            stats=stats,
            days=days
        )
        
    except Exception as e:
        logger.error(f"Failed to get price history for product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price history"
        )


@router.get("/product/{product_id}/stats", response_model=PriceStatsResponse)
async def get_product_price_stats(
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to calculate stats for"),
    db: Session = Depends(get_db)
):
    """
    Get price statistics for a specific product
    """
    try:
        price_service = PriceService(db)
        
        stats = await price_service.get_product_price_stats(
            product_id=product_id,
            days=days
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get price stats for product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price statistics"
        )


@router.get("/trends/popular", response_model=List[dict])
async def get_popular_price_trends(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    category: Optional[str] = Query(None, description="Filter by category"),
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    limit: int = Query(20, ge=1, le=100, description="Number of trends to return"),
    db: Session = Depends(get_db)
):
    """
    Get popular price trends across products
    """
    try:
        price_service = PriceService(db)
        
        trends = await price_service.get_popular_price_trends(
            platform=platform,
            category=category,
            days=days,
            limit=limit
        )
        
        return trends
        
    except Exception as e:
        logger.error(f"Failed to get popular price trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price trends"
        )


@router.get("/alerts/price-drops", response_model=List[dict])
async def get_price_drops(
    threshold_percentage: float = Query(5.0, ge=0.1, le=50.0, description="Minimum percentage drop to include"),
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=200, description="Number of price drops to return"),
    db: Session = Depends(get_db)
):
    """
    Get products with significant price drops
    """
    try:
        price_service = PriceService(db)
        
        price_drops = await price_service.get_price_drops(
            threshold_percentage=threshold_percentage,
            days=days,
            limit=limit
        )
        
        return price_drops
        
    except Exception as e:
        logger.error(f"Failed to get price drops: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price drops"
        )


@router.get("/alerts/price-increases", response_model=List[dict])
async def get_price_increases(
    threshold_percentage: float = Query(5.0, ge=0.1, le=50.0, description="Minimum percentage increase to include"),
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=200, description="Number of price increases to return"),
    db: Session = Depends(get_db)
):
    """
    Get products with significant price increases
    """
    try:
        price_service = PriceService(db)
        
        price_increases = await price_service.get_price_increases(
            threshold_percentage=threshold_percentage,
            days=days,
            limit=limit
        )
        
        return price_increases
        
    except Exception as e:
        logger.error(f"Failed to get price increases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price increases"
        )


@router.get("/comparison/{product_id1}/{product_id2}", response_model=dict)
async def compare_product_prices(
    product_id1: int,
    product_id2: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to compare"),
    db: Session = Depends(get_db)
):
    """
    Compare prices between two products
    """
    try:
        price_service = PriceService(db)
        
        comparison = await price_service.compare_product_prices(
            product_id1=product_id1,
            product_id2=product_id2,
            days=days
        )
        
        return comparison
        
    except Exception as e:
        logger.error(f"Failed to compare products {product_id1} and {product_id2}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare product prices"
        )


@router.post("/cleanup/old-prices", response_model=dict)
async def cleanup_old_prices(
    days_to_keep: int = Query(90, ge=30, le=365, description="Number of days of price data to keep"),
    db: Session = Depends(get_db)
):
    """
    Clean up old price data to save storage space
    """
    try:
        price_service = PriceService(db)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted_count = await price_service.cleanup_old_prices(cutoff_date)
        
        logger.info(f"Cleaned up {deleted_count} old price records")
        return {
            "message": f"Cleaned up {deleted_count} old price records",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old prices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup old prices"
        )
