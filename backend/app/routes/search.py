"""
Product search API routes across multiple platforms (Firebase version)
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.product import SearchQuery, SearchResponse, SearchResultItem
from app.services.scraping_service import ScrapingService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
scraping_service = ScrapingService()


@router.post("/search", response_model=SearchResponse)
async def search_products(body: SearchQuery):
    """
    Search products across supported platforms concurrently.
    Results are not stored in SQL — Firestore can optionally store search history.
    """
    try:
        platforms = [p.value for p in body.platforms] if body.platforms else None
        raw_results = await scraping_service.search_products(
            query=body.query,
            limit_per_platform=body.limit_per_platform,
            platforms=platforms,
        )

        items = [SearchResultItem(**r) for r in raw_results]

        # (Optional) Save the search query to Firestore for analytics
        try:
            from firebase_admin import firestore

            db = firestore.client()
            db.collection("search_history").add(
                {
                    "query": body.query,
                    "platforms": platforms,
                    "timestamp": firestore.SERVER_TIMESTAMP,
                    "results_count": len(items),
                }
            )
        except Exception as e:
            logger.warning(f"Could not log search to Firestore: {e}")

        return SearchResponse(query=body.query, results=items)

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search products",
        )
