from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Customer
from app.schemas import CustomerCreate, CustomerOut, LoginInput, TokenOut
from app.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# ── Shadow endpoint: signup is real but hidden from OpenAPI docs ──────────────
@router.post(
    "/signup",
    response_model=CustomerOut,
    status_code=201,
    include_in_schema=False,   # <-- shadow: works but never shows in Swagger
    summary="Create a customer account",
)
def signup(data: CustomerCreate, db: Session = Depends(get_db)):
    if db.query(Customer).filter_by(email=data.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    customer = Customer(
        name=data.name.strip(),
        email=data.email.lower(),
        password_hash=hash_password(data.password),
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


# ── Documented endpoint ───────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=TokenOut,
    summary="Authenticate and receive a bearer token",
    responses={401: {"description": "Invalid credentials"}},
)
def login(data: LoginInput, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter_by(email=data.email.lower()).first()
    if not customer or not verify_password(data.password, customer.password_hash):
        raise HTTPException(401, "Invalid email or password")
    token, _, exp = create_access_token(customer.id)
    return TokenOut(
        access_token=token,
        expires_in=max(0, int((exp - datetime.now(timezone.utc)).total_seconds())),
    )
