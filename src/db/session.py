"""
Database session management.
SQLAlchemy async session factory.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from src.config import get_settings

settings = get_settings()

# Use SQLite for development if no DATABASE_URL is set
_url = settings.database_url or "sqlite:///./kiyasgo_dev.db"

# Adjust for SQLite (no asyncpg needed)
if _url.startswith("sqlite"):
    engine = create_engine(_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_db():
    """
    Dependency that yields a database session.
    Usage in FastAPI:
        @router.get("/foo")
        def foo(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Call once at startup."""
    Base.metadata.create_all(bind=engine)
