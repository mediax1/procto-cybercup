from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from app.database import get_db
from app.models import Customer, RevokedToken
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)
def get_current_customer(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> Customer:
    if credentials is None: raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate":"Bearer"})
    try: payload = decode_token(credentials.credentials); cid = int(payload["sub"]); jti = payload["jti"]
    except (JWTError, ValueError, KeyError, TypeError): raise HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate":"Bearer"})
    if db.query(RevokedToken).filter_by(jti=jti).first(): raise HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate":"Bearer"})
    customer = db.get(Customer, cid)
    if not customer: raise HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate":"Bearer"})
    return customer
