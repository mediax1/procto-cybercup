from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Customer
from app.schemas import CustomerOut

router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])


# ── Shadow endpoint: no authentication required, exposes any customer profile ─
@router.get(
    "/{customer_id}",
    response_model=CustomerOut,
    include_in_schema=False,   # <-- shadow: broken object-level auth (no auth at all)
    summary="Get any customer profile — no authentication enforced",
)
def get_customer_unauthenticated(customer_id: int, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    return customer
