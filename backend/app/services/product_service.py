"""
Product service using Firebase Firestore
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
import uuid
from app.firebase import db



class ProductService:
    COLLECTION = "products"

    def __init__(self, _db=None):
        self.collection = db.collection(self.COLLECTION)

    async def create_product(self, data) -> Dict:
        product_id = str(uuid.uuid4())
        product_data = {
            "id": product_id,
            "name": data.name,
            "description": getattr(data, "description", ""),
            "product_url": data.product_url,
            "platform": data.platform,
            "category": getattr(data, "category", ""),
            "brand": getattr(data, "brand", ""),
            "current_price": None,
            "currency": "INR",
            "is_tracking": True,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self.collection.document(product_id).set(product_data)
        return product_data

    async def list_products(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict] = None
    ) -> Tuple[List[Dict], int]:
        query = self.collection
        if filters:
            if filters.get("platform"):
                query = query.where("platform", "==", filters["platform"])
            if filters.get("category"):
                query = query.where("category", "==", filters["category"])
            if filters.get("brand"):
                query = query.where("brand", "==", filters["brand"])
            if filters.get("is_tracking") is not None:
                query = query.where("is_tracking", "==", filters["is_tracking"])

        docs = query.stream()
        all_products = []
        for doc in docs:
            product = doc.to_dict()
            if filters.get("search"):
                if filters["search"].lower() not in product.get("name", "").lower():
                    continue
            all_products.append(product)

        total = len(all_products)
        return all_products[skip : skip + limit], total

    async def get_product(self, product_id: str) -> Optional[Dict]:
        doc = self.collection.document(product_id).get()
        return doc.to_dict() if doc.exists else None

    async def update_product(self, product_id: str, data) -> Optional[Dict]:
        ref = self.collection.document(product_id)
        doc = ref.get()
        if not doc.exists:
            return None

        update_data = {**doc.to_dict(), **data.dict(exclude_unset=True)}
        update_data["updated_at"] = datetime.utcnow().isoformat()
        ref.set(update_data)
        return update_data

    async def delete_product(self, product_id: str) -> bool:
        doc_ref = self.collection.document(product_id)
        if not doc_ref.get().exists:
            return False
        doc_ref.delete()
        return True

    async def update_tracking_status(self, product_id: str, new_status: bool):
        ref = self.collection.document(product_id)
        if not ref.get().exists:
            return False
        ref.update(
            {
                "is_tracking": new_status,
                "updated_at": datetime.utcnow().isoformat(),
            }
        )
        return True

    async def get_last_scraped_time(self, product_id: str):
        doc = self.collection.document(product_id).get()
        if doc.exists:
            return datetime.fromisoformat(doc.to_dict().get("updated_at"))
        return None

    async def get_price_history(
        self, product_id: str, days: int = 30, limit: int = 100
    ):
        prices_ref = (
            db.collection("prices")
            .where("product_id", "==", product_id)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        prices = [doc.to_dict() for doc in prices_ref.stream()]
        return prices
