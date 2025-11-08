"""
Data cleanup background task (Firebase Firestore version)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from firebase_admin import firestore
from app.services.price_service import PriceService
from config import settings

logger = logging.getLogger(__name__)
db = firestore.client()


class CleanupTask:
    """
    Background task for cleaning up old Firestore data
    """

    def __init__(self):
        self.last_run = None
        self.is_running = False
        self.price_service = PriceService()

    # ---------------------------------------------------
    # Main Cleanup Runner
    # ---------------------------------------------------
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run cleanup job for all data collections
        """
        if self.is_running:
            logger.warning("Cleanup task is already running")
            return {"status": "already_running"}

        try:
            self.is_running = True
            self.last_run = datetime.utcnow()
            logger.info("🧹 Starting Firestore data cleanup task")

            days_to_keep = kwargs.get("days_to_keep", settings.MAX_PRICE_HISTORY_DAYS)
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            # Clean prices
            deleted_prices = await self.price_service.cleanup_old_prices(days_to_keep)

            # Clean scraping sessions
            deleted_sessions = await self._cleanup_collection("scraping_sessions", cutoff_date)

            # Clean scraping errors
            deleted_errors = await self._cleanup_collection("scraping_errors", cutoff_date)

            result = {
                "deleted_prices": deleted_prices,
                "deleted_sessions": deleted_sessions,
                "deleted_errors": deleted_errors,
                "cutoff_date": cutoff_date.isoformat(),
            }

            logger.info(f"✅ Cleanup completed: {result}")
            return {"status": "completed", "result": result}

        except Exception as e:
            logger.error(f"❌ Cleanup task failed: {e}")
            return {"status": "failed", "error": str(e)}
        finally:
            self.is_running = False

    # ---------------------------------------------------
    # Specific Data Cleanup
    # ---------------------------------------------------
    async def cleanup_specific_data(self, data_type: str, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Clean up only one data type (prices, sessions, or errors)
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            if data_type == "prices":
                deleted_count = await self.price_service.cleanup_old_prices(days_to_keep)
            elif data_type == "sessions":
                deleted_count = await self._cleanup_collection("scraping_sessions", cutoff_date)
            elif data_type == "errors":
                deleted_count = await self._cleanup_collection("scraping_errors", cutoff_date)
            else:
                return {"status": "failed", "error": f"Unknown data type: {data_type}"}

            return {
                "status": "completed",
                "data_type": data_type,
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to cleanup {data_type}: {e}")
            return {"status": "failed", "error": str(e)}

    # ---------------------------------------------------
    # Collection Cleanup Utility
    # ---------------------------------------------------
    async def _cleanup_collection(self, collection_name: str, cutoff_date: datetime) -> int:
        """
        Helper to delete old documents from a Firestore collection
        """
        try:
            collection_ref = db.collection(collection_name)
            docs = list(collection_ref.stream())
            deleted_count = 0

            for doc in docs:
                data = doc.to_dict()
                created_at = data.get("created_at")
                if created_at and isinstance(created_at, datetime) and created_at < cutoff_date:
                    collection_ref.document(doc.id).delete()
                    deleted_count += 1

            logger.info(f"🧽 Deleted {deleted_count} old docs from {collection_name}")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup {collection_name}: {e}")
            return 0

    # ---------------------------------------------------
    # Cleanup Stats
    # ---------------------------------------------------
    async def get_cleanup_stats(self) -> Dict[str, Any]:
        """
        Get a summary of old records in Firestore collections
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=settings.MAX_PRICE_HISTORY_DAYS)

            old_prices = await self._count_old_docs("prices", cutoff_date)
            old_sessions = await self._count_old_docs("scraping_sessions", cutoff_date)
            old_errors = await self._count_old_docs("scraping_errors", cutoff_date)

            stats = {
                "old_prices": old_prices,
                "old_sessions": old_sessions,
                "old_errors": old_errors,
                "cutoff_date": cutoff_date.isoformat(),
                "days_to_keep": settings.MAX_PRICE_HISTORY_DAYS,
            }

            return {"status": "completed", "stats": stats}
        except Exception as e:
            logger.error(f"Failed to get cleanup stats: {e}")
            return {"status": "failed", "error": str(e)}

    # ---------------------------------------------------
    # Count Utility
    # ---------------------------------------------------
    async def _count_old_docs(self, collection_name: str, cutoff_date: datetime) -> int:
        """
        Count old documents for cleanup statistics
        """
        try:
            docs = list(db.collection(collection_name).stream())
            count = sum(
                1
                for doc in docs
                if doc.to_dict().get("created_at")
                and isinstance(doc.to_dict()["created_at"], datetime)
                and doc.to_dict()["created_at"] < cutoff_date
            )
            return count
        except Exception as e:
            logger.error(f"Failed to count old docs in {collection_name}: {e}")
            return 0
