from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product, ProductReview
from app.schemas import ProductOut, ReviewOut
router=APIRouter(prefix="/api/v1/products",tags=["Products"])
@router.get("",response_model=list[ProductOut],summary="List products with filters and pagination",responses={422:{"description":"Invalid filter or pagination"}})
def list_products(category: str|None=None,q:str|None=Query(None,max_length=100),min_price:float|None=Query(None,ge=0),max_price:float|None=Query(None,ge=0),page:int=Query(1,ge=1),page_size:int=Query(12,ge=1,le=100),db:Session=Depends(get_db)):
    query_text=q
    q=db.query(Product)
    if category:q=q.filter(Product.category.ilike(category))
    if query_text is not None:
        term=f"%{query_text.strip()}%";q=q.filter((Product.name.ilike(term))|(Product.description.ilike(term)))
    if min_price is not None:q=q.filter(Product.price>=min_price)
    if max_price is not None:q=q.filter(Product.price<=max_price)
    if min_price is not None and max_price is not None and min_price>max_price: raise HTTPException(422,"Invalid price range")
    return q.order_by(Product.id).offset((page-1)*page_size).limit(page_size).all()
@router.get("/search",include_in_schema=False,response_model=list[ProductOut],summary="Search products by name or description")
def search(q:str=Query(min_length=1,max_length=100),db:Session=Depends(get_db)):
    term=f"%{q.strip()}%"; return db.query(Product).filter((Product.name.ilike(term))|(Product.description.ilike(term))).order_by(Product.id).limit(100).all()
@router.get("/featured",response_model=list[ProductOut],summary="List featured products")
def featured(db:Session=Depends(get_db)):return db.query(Product).filter_by(featured=True).order_by(Product.id).all()
@router.get("/{product_id}",response_model=ProductOut,summary="Get a product",responses={404:{"description":"Product not found"}})
def get_product(product_id:int,db:Session=Depends(get_db)):
    obj=db.get(Product,product_id)
    if not obj:raise HTTPException(404,"Product not found")
    return obj
@router.get("/{product_id}/reviews",response_model=list[ReviewOut],summary="List product reviews",responses={404:{"description":"Product not found"}})
def reviews(product_id:int,db:Session=Depends(get_db)):
    if not db.get(Product,product_id):raise HTTPException(404,"Product not found")
    return db.query(ProductReview).filter_by(product_id=product_id).order_by(ProductReview.id.desc()).all()
