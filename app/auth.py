import os
import secrets
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request, status
from jose import jwt, JWTError
from sqlmodel import Session, select

from app.models import AdminUser, engine, pwd_context

# In production set this via an environment variable — never hardcode a real one.
def _load_secret_key() -> str:
    """SECRET_KEY env var if set, otherwise a random key created once and kept in
    .secret_key (git-ignored) so it never appears in the repository."""
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".secret_key")
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(path, "w") as f:
        f.write(key)
    return key


SECRET_KEY = _load_secret_key()
ALGORITHM = "HS256"
COOKIE_NAME = "admin_session"
TOKEN_EXPIRE_HOURS = 12


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_admin(username: str, password: str) -> bool:
    with Session(engine) as session:
        user = session.exec(select(AdminUser).where(AdminUser.username == username)).first()
        if not user:
            return False
        return verify_password(password, user.password_hash)


def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def require_admin(request: Request) -> str:
    """FastAPI dependency: raises 401 if the request has no valid admin session."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise JWTError()
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
