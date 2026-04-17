"""Shared dependencies for API routes - database session injection"""
import logging
from sqlalchemy.orm import Session
from fastapi import Depends

from src.core.database import get_db
from src.weaviate_service import get_weaviate_service

logger = logging.getLogger(__name__)


def get_session(db: Session = Depends(get_db)) -> Session:
    """Get database session for routes"""
    return db


def get_weaviate():
    """Get Weaviate service instance"""
    return get_weaviate_service()
