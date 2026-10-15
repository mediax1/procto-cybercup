from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from app.database import get_db, next_id
from app.schemas import CustomerCreate, CustomerOut, LoginInput, TokenOut
from app.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/signup", response_model=CustomerOut, status_code=201, include_in_schema=False, summary="Create a customer account")
def signup(data: CustomerCreate, db=Depends(get_db)):
    email = data.email.lower()
    if db.customers.find_one({"email": email}):
        raise HTTPException(409, "Email already registered")
    customer = {"id": next_id(db.customers), "name": data.name.strip(), "email": email, "password_hash": hash_password(data.password), "created_at": datetime.now(timezone.utc)}
    try:
        db.customers.insert_one(customer)
    except DuplicateKeyError:
        raise HTTPException(409, "Email already registered")
    return {key: value for key, value in customer.items() if key != "password_hash"}

@router.post("/login", response_model=TokenOut, summary="Authenticate and receive a bearer token", responses={401: {"description": "Invalid credentials"}})
def login(data: LoginInput, db=Depends(get_db)):
    customer = db.customers.find_one({"email": data.email.lower()})
    if not customer or not verify_password(data.password, customer["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    token, _, exp = create_access_token(customer["id"])
    return TokenOut(access_token=token, expires_in=max(0, int((exp - datetime.now(timezone.utc)).total_seconds())))

