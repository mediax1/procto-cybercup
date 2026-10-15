from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product
from app.schemas import ProductOut

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


# ── Documented endpoint ───────────────────────────────────────────────────────
@router.get(
    "",
    response_model=list[ProductOut],
    summary="List products with optional filters and pagination",
    responses={422: {"description": "Invalid filter or pagination parameters"}},
)
def list_products(
    category: str | None = None,
    q: str | None = Query(None, max_length=100),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(422, "min_price must be <= max_price")

    query = db.query(Product)
    if category:
        query = query.filter(Product.category.ilike(category))
    if q is not None:
        term = f"%{q.strip()}%"
        query = query.filter(
            (Product.name.ilike(term)) | (Product.description.ilike(term))
        )
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    return (
        query.order_by(Product.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
