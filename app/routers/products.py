import re
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_db

router = APIRouter(prefix="/api/v1/products", tags=["Products"])

@router.get("", summary="List products with optional filters and pagination")
def list_products(category: str | None = None, q: str | None = Query(None, max_length=100), min_price: float | None = Query(None, ge=0), max_price: float | None = Query(None, ge=0), page: int = Query(1, ge=1), page_size: int = Query(12, ge=1, le=100), db=Depends(get_db)):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(422, "min_price must be <= max_price")
    query = {}
    if category:
        query["category"] = {"$regex": f"^{re.escape(category)}$", "$options": "i"}
    if q is not None:
        term = re.escape(q.strip())
        query["$or"] = [{"name": {"$regex": term, "$options": "i"}}, {"description": {"$regex": term, "$options": "i"}}]
    price = {}
    if min_price is not None:
        price["$gte"] = min_price
    if max_price is not None:
        price["$lte"] = max_price
    if price:
        query["price"] = price
    cursor = db.products.find(query, {"_id": 0}).sort("id", 1).skip((page - 1) * page_size).limit(page_size)
    return list(cursor)

