"""
Product search API routes across multiple platforms
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.product import SearchQuery, SearchResponse, SearchResultItem
from app.services.scraping_service import ScrapingService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_products(
    body: SearchQuery,
    db: Session = Depends(get_db)
):
    """
    Search products across supported platforms concurrently.
    """
    try:
        scraping_service = ScrapingService(db)
        platforms = [p.value for p in body.platforms] if body.platforms else None
        raw_results = await scraping_service.search_products(
            query=body.query,
            limit_per_platform=body.limit_per_platform,
            platforms=platforms
        )
        items = [SearchResultItem(**r) for r in raw_results]
        return SearchResponse(query=body.query, results=items)
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search products"
        )


