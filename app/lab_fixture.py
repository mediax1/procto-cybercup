from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_customer
from app.models import Order, Customer
router=APIRouter()
@router.get("/api/lab/orders/{order_id}",include_in_schema=False)
def intentionally_unsafe_order(order_id:int,db:Session=Depends(get_db),customer:Customer=Depends(get_current_customer)):
    order=db.get(Order,order_id)
    if not order:raise HTTPException(404,"Order not found")
    return {"id":order.id,"customer_id":order.customer_id,"status":order.status,"total":order.total}
