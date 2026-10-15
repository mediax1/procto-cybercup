from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.dependencies import get_current_customer

router = APIRouter()

@router.get("/api/lab/orders/{order_id}", include_in_schema=False)
def intentionally_unsafe_order(order_id: int, db=Depends(get_db), customer=Depends(get_current_customer)):
    order = db.orders.find_one({"id": order_id}, {"_id": 0, "items": 0})
    if not order:
        raise HTTPException(404, "Order not found")
    return {"id": order["id"], "customer_id": order["customer_id"], "status": order["status"], "total": order["total"]}

