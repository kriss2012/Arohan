from datetime import datetime, timezone, timedelta
from typing import Any, Union, Optional
import jwt
import bcrypt
from backend.app.core.config import settings

def get_server_time_utc() -> datetime:
    """Returns authoritative server UTC time."""
    return datetime.now(timezone.utc)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def create_access_token(subject: Union[str, Any], roles: list[str], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = get_server_time_utc() + expires_delta
    else:
        expire = get_server_time_utc() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "iat": get_server_time_utc(),
        "sub": str(subject),
        "roles": roles,
        "type": "access"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = get_server_time_utc() + expires_delta
    else:
        expire = get_server_time_utc() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "exp": expire,
        "iat": get_server_time_utc(),
        "sub": str(subject),
        "type": "refresh"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_setup_token(subject: str, email: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = get_server_time_utc() + (expires_delta or timedelta(minutes=15))
    to_encode = {
        "exp": expire,
        "iat": get_server_time_utc(),
        "sub": str(subject),
        "email": email,
        "purpose": "password_setup"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None
