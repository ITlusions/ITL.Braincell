from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator

from src.core.config import get_settings
from src.core.models import Base

settings = get_settings()

# Create engine with connection pooling disabled for development
engine = create_engine(
    settings.database_url,
    poolclass=NullPool if settings.debug else None,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all tables (use with caution)"""
    Base.metadata.drop_all(bind=engine)
