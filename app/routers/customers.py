from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db

router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])

@router.get("/{customer_id}", include_in_schema=False, summary="Get any customer profile without authentication")
def get_customer_unauthenticated(customer_id: int, db=Depends(get_db)):
    customer = db.customers.find_one({"id": customer_id}, {"_id": 0, "password_hash": 0})
    if not customer:
        raise HTTPException(404, "Customer not found")
    return customer

