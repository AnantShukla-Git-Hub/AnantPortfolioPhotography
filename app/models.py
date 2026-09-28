import os
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, create_engine, Session
from passlib.context import CryptContext

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "portfolio.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Photo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    base_id: str  # shared prefix for the 3 saved size variants on disk
    url: str  # full-size (largest) variant
    url_medium: str
    url_thumb: str
    caption: Optional[str] = None
    is_featured: bool = False
    featured_order: Optional[int] = None
    gallery_order: int = 0
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class AdminUser(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    password_hash: str


def init_db():
    """Create tables and seed the single admin account if none exists."""
    SQLModel.metadata.create_all(engine)
    from sqlmodel import select

    with Session(engine) as session:
        existing = session.exec(select(AdminUser)).first()
        if not existing:
            username = os.environ.get("ADMIN_USERNAME", "admin")
            password = os.environ.get("ADMIN_PASSWORD", "changeme123")
            admin = AdminUser(
                username=username,
                password_hash=pwd_context.hash(password),
            )
            session.add(admin)
            session.commit()
            print(
                f"[init_db] Created default admin user '{username}'. "
                f"Set ADMIN_USERNAME / ADMIN_PASSWORD env vars before real use."
            )


def get_session():
    with Session(engine) as session:
        yield session
