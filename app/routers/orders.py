from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.dependencies import get_current_customer
from app.models import Customer, Order, OrderItem, Product
from app.schemas import OrderCreate, OrderPatch, OrderOut
router=APIRouter(prefix="/api/v1/orders",tags=["Orders"])
def owned_order(order_id:int,db:Session,c:Customer):
    order=db.query(Order).options(joinedload(Order.items)).filter_by(id=order_id).first()
    if not order:raise HTTPException(404,"Order not found")
    if order.customer_id!=c.id:raise HTTPException(403,"Access denied")
    return order
@router.post("",response_model=OrderOut,status_code=201,summary="Create an order",responses={401:{"description":"Authentication required"},422:{"description":"Invalid items or insufficient stock"}})
def create_order(data:OrderCreate,db:Session=Depends(get_db),c:Customer=Depends(get_current_customer)):
    quantities={}
    for item in data.items:quantities[item.product_id]=quantities.get(item.product_id,0)+item.quantity
    products={p.id:p for p in db.query(Product).filter(Product.id.in_(quantities)).all()}
    if len(products)!=len(quantities):raise HTTPException(422,"One or more products are unavailable")
    for pid,qty in quantities.items():
        if products[pid].stock<qty:raise HTTPException(422,"Insufficient stock")
    total=sum(products[i.product_id].price*i.quantity for i in data.items)
    order=Order(customer_id=c.id,status="pending",payment_status="authorized",total=round(total,2),shipping_address=data.shipping_address)
    db.add(order);db.flush()
    for item in data.items:
        product=products[item.product_id];product.stock-=item.quantity
        db.add(OrderItem(order_id=order.id,product_id=product.id,product_name=product.name,quantity=item.quantity,unit_price=product.price))
    db.commit();return owned_order(order.id,db,c)
@router.get("",response_model=list[OrderOut],summary="List your orders")
def list_orders(db:Session=Depends(get_db),c:Customer=Depends(get_current_customer)):
    return db.query(Order).options(joinedload(Order.items)).filter_by(customer_id=c.id).order_by(Order.created_at.desc()).all()
@router.get("/{order_id}",response_model=OrderOut,summary="Get an order you own",responses={403:{"description":"Access denied"},404:{"description":"Order not found"}})
def get_order(order_id:int,db:Session=Depends(get_db),c:Customer=Depends(get_current_customer)):return owned_order(order_id,db,c)
@router.patch("/{order_id}",response_model=OrderOut,summary="Update permitted order fields",responses={403:{"description":"Access denied"},404:{"description":"Order not found"},409:{"description":"Order cannot be modified"}})
def patch_order(order_id:int,data:OrderPatch,db:Session=Depends(get_db),c:Customer=Depends(get_current_customer)):
    order=owned_order(order_id,db,c)
    if order.status!="pending":raise HTTPException(409,"Only pending orders can be modified")
    order.shipping_address=data.shipping_address;db.commit();return owned_order(order_id,db,c)
@router.post("/{order_id}/cancel",response_model=OrderOut,summary="Cancel a pending order",responses={403:{"description":"Access denied"},404:{"description":"Order not found"},409:{"description":"Order cannot be cancelled"}})
def cancel_order(order_id:int,db:Session=Depends(get_db),c:Customer=Depends(get_current_customer)):
    order=owned_order(order_id,db,c)
    if order.status!="pending":raise HTTPException(409,"Only pending orders can be cancelled")
    order.status="cancelled";order.payment_status="voided"
    for item in order.items:
        p=db.get(Product,item.product_id)
        if p:p.stock+=item.quantity
    db.commit();return owned_order(order_id,db,c)
@router.get("/{order_id}/tracking",summary="View synthetic tracking events",responses={403:{"description":"Access denied"},404:{"description":"Order not found"}})
def tracking(order_id:int,db:Session=Depends(get_db),c:Customer=Depends(get_current_customer)):
    order=owned_order(order_id,db,c);base=order.created_at
    events=[{"status":"Order placed","occurred_at":base.isoformat()}]
    if order.status in ("shipped","delivered"):events.append({"status":"Package shipped","occurred_at":base.isoformat()})
    if order.status=="delivered":events.append({"status":"Delivered","occurred_at":datetime.now(timezone.utc).isoformat()})
    if order.status=="cancelled":events.append({"status":"Order cancelled","occurred_at":datetime.now(timezone.utc).isoformat()})
    return {"order_id":order.id,"status":order.status,"events":events}
