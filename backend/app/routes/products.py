"""
Product management API routes (Firebase Firestore version)
"""

from fastapi import APIRouter, HTTPException, Query, status, Depends, Header
from typing import Optional
import logging
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse
from app.services.product_service import ProductService
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter()
product_service = ProductService()
auth_service = AuthService()

# ---------------------------------------------------
# Firebase Auth Dependency
# ---------------------------------------------------
async def verify_token(authorization: str = Header(...)):
    """
    Dependency that verifies Firebase ID token
    """
    try:
        token = authorization.split(" ")[1]
        decoded_token = await auth_service.verify_firebase_token(token)
        return decoded_token  # contains uid, email, etc.
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or missing token")


# ---------------------------------------------------
# Routes
# ---------------------------------------------------
@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    user=Depends(verify_token),
):
    """
    Create a new product for price tracking (authenticated)
    """
    try:
        product = await product_service.create_product(product_data)
        logger.info(f"Created product: {product['id']} - {product['name']}")
        return product
    except Exception as e:
        logger.error(f"Failed to create product: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=ProductListResponse)
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    platform: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    is_tracking: Optional[bool] = None,
    search: Optional[str] = None,
    user=Depends(verify_token),  # 🔒 Protected route
):
    """
    List products with filtering and pagination (from Firestore)
    """
    try:
        filters = {
            "platform": platform,
            "category": category,
            "brand": brand,
            "is_tracking": is_tracking,
            "search": search,
        }
        products, total = await product_service.list_products(skip, limit, filters)
        return ProductListResponse(
            products=products, total=total, skip=skip, limit=limit
        )
    except Exception as e:
        logger.error(f"Failed to list products: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve products")


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, user=Depends(verify_token)):
    """
    Get a specific product by ID
    """
    product = await product_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    user=Depends(verify_token),
):
    """
    Update a product
    """
    product = await product_service.update_product(product_id, product_data)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: str, user=Depends(verify_token)):
    """
    Delete a product
    """
    success = await product_service.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    logger.info(f"Deleted product: {product_id}")
    return {"message": "Product deleted successfully"}


@router.post("/{product_id}/toggle-tracking", response_model=dict)
async def toggle_tracking(product_id: str, user=Depends(verify_token)):
    """
    Toggle tracking on/off
    """
    product = await product_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_status = not product.get("is_tracking", False)
    await product_service.update_tracking_status(product_id, new_status)
    return {
        "product_id": product_id,
        "is_tracking": new_status,
        "message": f"Tracking {'enabled' if new_status else 'disabled'}",
    }
