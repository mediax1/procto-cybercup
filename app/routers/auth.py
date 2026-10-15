from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Customer, PasswordResetToken, RevokedToken
from app.schemas import CustomerCreate, CustomerOut, LoginInput, ForgotPasswordInput, ResetPasswordInput, TokenOut, MessageOut
from app.security import hash_password, verify_password, create_access_token, decode_token, new_reset_token, hash_reset_token
from app.config import settings
from app.dependencies import get_current_customer, bearer
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
@router.post("/signup", response_model=CustomerOut, status_code=201, summary="Create a customer account", responses={409:{"description":"Email already registered"},422:{"description":"Validation error"}})
def signup(data: CustomerCreate, db: Session = Depends(get_db)):
    if db.query(Customer).filter_by(email=data.email.lower()).first(): raise HTTPException(409, "Email already registered")
    customer=Customer(name=data.name.strip(),email=data.email.lower(),password_hash=hash_password(data.password)); db.add(customer); db.commit(); db.refresh(customer); return customer
@router.post("/login", response_model=TokenOut, summary="Authenticate and receive a bearer token", responses={401:{"description":"Invalid credentials"}})
def login(data: LoginInput, db: Session = Depends(get_db)):
    customer=db.query(Customer).filter_by(email=data.email.lower()).first()
    if not customer or not verify_password(data.password,customer.password_hash): raise HTTPException(401,"Invalid email or password")
    token,_,exp=create_access_token(customer.id); return TokenOut(access_token=token,expires_in=max(0,int((exp-datetime.now(timezone.utc)).total_seconds())))
@router.post("/logout", response_model=MessageOut, summary="Revoke the current bearer token", responses={401:{"description":"Authentication required"}})
def logout(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)):
    if not credentials: raise HTTPException(401,"Authentication required")
    try: payload=decode_token(credentials.credentials)
    except (JWTError,ValueError,KeyError): raise HTTPException(401,"Invalid or expired token")
    if not db.query(RevokedToken).filter_by(jti=payload["jti"]).first():
        exp=datetime.fromtimestamp(payload["exp"],timezone.utc); db.add(RevokedToken(jti=payload["jti"],expires_at=exp)); db.commit()
    return {"message":"Logged out"}
@router.post("/refresh", response_model=TokenOut, summary="Rotate the current bearer token", responses={401:{"description":"Authentication required"}})
def refresh(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), customer: Customer = Depends(get_current_customer), db: Session = Depends(get_db)):
    payload=decode_token(credentials.credentials)
    if not db.query(RevokedToken).filter_by(jti=payload["jti"]).first():
        db.add(RevokedToken(jti=payload["jti"],expires_at=datetime.fromtimestamp(payload["exp"],timezone.utc)));db.commit()
    token,_,exp=create_access_token(customer.id); return TokenOut(access_token=token,expires_in=max(0,int((exp-datetime.now(timezone.utc)).total_seconds())))
@router.post("/forgot-password", response_model=MessageOut, summary="Request a password reset", responses={422:{"description":"Validation error"}})
def forgot_password(data: ForgotPasswordInput, db: Session = Depends(get_db)):
    customer=db.query(Customer).filter_by(email=data.email.lower()).first()
    if customer:
        raw,digest=new_reset_token(); db.add(PasswordResetToken(customer_id=customer.id,token_hash=digest,expires_at=datetime.now(timezone.utc)+timedelta(minutes=settings.reset_token_minutes))); db.commit()
        print(f"[password-reset] customer_id={customer.id} token={raw}", flush=True)
    return {"message":"If the account exists, reset instructions have been issued"}
@router.post("/reset-password", response_model=MessageOut, summary="Set a new password using a one-time reset token", responses={400:{"description":"Invalid, expired, or used reset token"}})
def reset_password(data: ResetPasswordInput, db: Session = Depends(get_db)):
    row=db.query(PasswordResetToken).filter_by(token_hash=hash_reset_token(data.token),used=False).first()
    if not row or row.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc): raise HTTPException(400,"Reset token is invalid or expired")
    customer=db.get(Customer,row.customer_id); customer.password_hash=hash_password(data.new_password); row.used=True; db.commit(); return {"message":"Password updated"}
@router.get("/me", response_model=CustomerOut, summary="Get the authenticated customer", responses={401:{"description":"Authentication required"}})
def me(customer: Customer = Depends(get_current_customer)): return customer
