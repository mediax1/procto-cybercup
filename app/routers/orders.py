from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.dependencies import get_current_customer
from app.models import Customer, Order, OrderItem, Product
from app.schemas import OrderCreate, OrderOut

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


# ── Documented endpoint ───────────────────────────────────────────────────────
@router.post(
    "",
    response_model=OrderOut,
    status_code=201,
    summary="Place an order",
    responses={
        401: {"description": "Authentication required"},
        422: {"description": "Invalid items or insufficient stock"},
    },
)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    c: Customer = Depends(get_current_customer),
):
    # Aggregate quantities per product so duplicate line-items are merged
    quantities: dict[int, int] = {}
    for item in data.items:
        quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity

    products = {
        p.id: p
        for p in db.query(Product).filter(Product.id.in_(quantities)).all()
    }
    if len(products) != len(quantities):
        raise HTTPException(422, "One or more products are unavailable")
    for pid, qty in quantities.items():
        if products[pid].stock < qty:
            raise HTTPException(422, f"Insufficient stock for product {pid}")

    total = sum(products[i.product_id].price * i.quantity for i in data.items)
    order = Order(
        customer_id=c.id,
        status="pending",
        payment_status="authorized",
        total=round(total, 2),
        shipping_address=data.shipping_address,
    )
    db.add(order)
    db.flush()

    for item in data.items:
        product = products[item.product_id]
        product.stock -= item.quantity
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                quantity=item.quantity,
                unit_price=product.price,
            )
        )

    db.commit()
    # Re-fetch with items eagerly loaded
    return (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter_by(id=order.id)
        .first()
    )


# ── Shadow endpoint: IDOR — no ownership check, hidden from docs ──────────────
@router.get(
    "/{order_id}",
    response_model=OrderOut,
    include_in_schema=False,   # <-- shadow
    summary="Get any order by ID (no ownership enforcement)",
)
def get_order_idor(
    order_id: int,
    db: Session = Depends(get_db),
    _: Customer = Depends(get_current_customer),  # auth required, ownership NOT checked
):
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter_by(id=order_id)
        .first()
    )
    if not order:
        raise HTTPException(404, "Order not found")
    return order
