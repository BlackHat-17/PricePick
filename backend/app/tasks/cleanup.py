"""
Data cleanup background task
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from app.database import get_db_session
from app.services.price_service import PriceService
from config import settings

logger = logging.getLogger(__name__)


class CleanupTask:
    """
    Background task for cleaning up old data
    """
    
    def __init__(self):
        self.last_run = None
        self.is_running = False
    
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the cleanup task
        """
        if self.is_running:
            logger.warning("Cleanup task is already running")
            return {"status": "already_running"}
        
        try:
            self.is_running = True
            self.last_run = datetime.utcnow()
            
            logger.info("Starting data cleanup task")
            
            # Get database session
            db = get_db_session()
            try:
                # Initialize price service
                price_service = PriceService(db)
                
                # Calculate cutoff date
                days_to_keep = kwargs.get('days_to_keep', settings.MAX_PRICE_HISTORY_DAYS)
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                
                # Clean up old prices
                deleted_prices = await price_service.cleanup_old_prices(cutoff_date)
                
                # Clean up old scraping sessions
                from app.models.scraping import ScrapingSession
                old_sessions = db.query(ScrapingSession).filter(
                    ScrapingSession.created_at < cutoff_date
                ).count()
                
                db.query(ScrapingSession).filter(
                    ScrapingSession.created_at < cutoff_date
                ).delete()
                
                # Clean up old scraping errors
                from app.models.scraping import ScrapingError
                old_errors = db.query(ScrapingError).filter(
                    ScrapingError.created_at < cutoff_date
                ).count()
                
                db.query(ScrapingError).filter(
                    ScrapingError.created_at < cutoff_date
                ).delete()
                
                db.commit()
                
                result = {
                    "deleted_prices": deleted_prices,
                    "deleted_sessions": old_sessions,
                    "deleted_errors": old_errors,
                    "cutoff_date": cutoff_date.isoformat()
                }
                
                logger.info(f"Cleanup completed: {result}")
                
                return {
                    "status": "completed",
                    "result": result
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Cleanup task failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
        finally:
            self.is_running = False
    
    async def cleanup_specific_data(self, data_type: str, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Clean up specific type of data
        """
        try:
            db = get_db_session()
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                
                if data_type == "prices":
                    price_service = PriceService(db)
                    deleted_count = await price_service.cleanup_old_prices(cutoff_date)
                    
                elif data_type == "sessions":
                    from app.models.scraping import ScrapingSession
                    deleted_count = db.query(ScrapingSession).filter(
                        ScrapingSession.created_at < cutoff_date
                    ).count()
                    
                    db.query(ScrapingSession).filter(
                        ScrapingSession.created_at < cutoff_date
                    ).delete()
                    db.commit()
                    
                elif data_type == "errors":
                    from app.models.scraping import ScrapingError
                    deleted_count = db.query(ScrapingError).filter(
                        ScrapingError.created_at < cutoff_date
                    ).count()
                    
                    db.query(ScrapingError).filter(
                        ScrapingError.created_at < cutoff_date
                    ).delete()
                    db.commit()
                    
                else:
                    return {
                        "status": "failed",
                        "error": f"Unknown data type: {data_type}"
                    }
                
                return {
                    "status": "completed",
                    "data_type": data_type,
                    "deleted_count": deleted_count,
                    "cutoff_date": cutoff_date.isoformat()
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to cleanup {data_type}: {str(e)}")
            return {
                "status": "failed",
                "data_type": data_type,
                "error": str(e)
            }
    
    async def get_cleanup_stats(self) -> Dict[str, Any]:
        """
        Get cleanup statistics
        """
        try:
            db = get_db_session()
            try:
                from app.models.price import Price
                from app.models.scraping import ScrapingSession, ScrapingError
                
                # Count old data
                cutoff_date = datetime.utcnow() - timedelta(days=settings.MAX_PRICE_HISTORY_DAYS)
                
                old_prices = db.query(Price).filter(
                    Price.created_at < cutoff_date
                ).count()
                
                old_sessions = db.query(ScrapingSession).filter(
                    ScrapingSession.created_at < cutoff_date
                ).count()
                
                old_errors = db.query(ScrapingError).filter(
                    ScrapingError.created_at < cutoff_date
                ).count()
                
                return {
                    "status": "completed",
                    "stats": {
                        "old_prices": old_prices,
                        "old_sessions": old_sessions,
                        "old_errors": old_errors,
                        "cutoff_date": cutoff_date.isoformat(),
                        "days_to_keep": settings.MAX_PRICE_HISTORY_DAYS
                    }
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to get cleanup stats: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
