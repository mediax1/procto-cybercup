from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db, next_id
from app.dependencies import get_current_customer
from app.schemas import OrderCreate

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])

@router.post("", status_code=201, summary="Place an order", responses={401: {"description": "Authentication required"}, 422: {"description": "Invalid items or insufficient stock"}})
def create_order(data: OrderCreate, db=Depends(get_db), customer=Depends(get_current_customer)):
    quantities = {}
    for item in data.items:
        quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity
    products = {p["id"]: p for p in db.products.find({"id": {"$in": list(quantities)}})}
    if len(products) != len(quantities):
        raise HTTPException(422, "One or more products are unavailable")
    for product_id, quantity in quantities.items():
        if products[product_id].get("stock", 0) < quantity:
            raise HTTPException(422, f"Insufficient stock for product {product_id}")
    reserved = []
    for product_id, quantity in quantities.items():
        result = db.products.update_one({"id": product_id, "stock": {"$gte": quantity}}, {"$inc": {"stock": -quantity}})
        if result.modified_count != 1:
            for reserved_id, reserved_quantity in reserved:
                db.products.update_one({"id": reserved_id}, {"$inc": {"stock": reserved_quantity}})
            raise HTTPException(422, f"Insufficient stock for product {product_id}")
        reserved.append((product_id, quantity))
    items = [{"product_id": item.product_id, "product_name": products[item.product_id]["name"], "quantity": item.quantity, "unit_price": products[item.product_id]["price"]} for item in data.items]
    order = {"id": next_id(db.orders), "customer_id": customer["id"], "status": "pending", "payment_status": "authorized", "total": round(sum(item["unit_price"] * item["quantity"] for item in items), 2), "created_at": datetime.now(timezone.utc), "shipping_address": data.shipping_address, "items": items}
    try:
        db.orders.insert_one(order)
    except Exception:
        for product_id, quantity in reserved:
            db.products.update_one({"id": product_id}, {"$inc": {"stock": quantity}})
        raise
    return {key: value for key, value in order.items() if key != "_id"}

@router.get("/{order_id}", include_in_schema=False, summary="Get any order by ID")
def get_order_idor(order_id: int, db=Depends(get_db), _=Depends(get_current_customer)):
    order = db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(404, "Order not found")
    return order

