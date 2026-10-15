import hashlib, secrets
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt
from app.config import settings

ALGORITHM = "HS256"
def hash_password(password: str) -> str: return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")
def verify_password(password: str, password_hash: str) -> bool:
    try: return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except Exception: return False
def create_access_token(customer_id: int, lifetime: timedelta | None = None) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc); exp = now + (lifetime or timedelta(minutes=settings.access_token_minutes)); jti = secrets.token_urlsafe(24)
    token = jwt.encode({"sub": str(customer_id), "jti": jti, "iat": now, "exp": exp}, settings.secret_key, algorithm=ALGORITHM)
    return token, jti, exp
def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM], options={"require_exp": True, "require_sub": True, "require_jti": True})
def new_reset_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)
    return raw, hashlib.sha256(raw.encode()).hexdigest()
def hash_reset_token(raw: str) -> str: return hashlib.sha256(raw.encode()).hexdigest()
