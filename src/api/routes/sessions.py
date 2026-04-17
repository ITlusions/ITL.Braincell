"""Memory Sessions entity routes - manage conversation context sessions"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core import models
from src.core.database import get_db
from src.core.schemas import MemorySessionCreate, MemorySessionResponse, MemorySessionUpdate
from src.services.weaviate_service import get_weaviate_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=MemorySessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session: MemorySessionCreate,
    db: Session = Depends(get_db),
):
    """Create a memory session and sync to vector database"""
    db_session = models.MemorySession(**session.model_dump())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # Sync to Weaviate vector database
    weaviate = get_weaviate_service()
    success = weaviate.index_memory_session(
        str(db_session.id),
        db_session.session_name,
        db_session.summary,
        db_session.status
    )
    
    if not success:
        logger.warning(f"Failed to sync memory session {db_session.id} to Weaviate")
    
    return db_session


@router.get("/{session_id}", response_model=MemorySessionResponse)
async def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a session by ID"""
    session = db.query(models.MemorySession).filter(models.MemorySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.put("/{session_id}", response_model=MemorySessionResponse)
async def update_session(
    session_id: UUID,
    session_update: MemorySessionUpdate,
    db: Session = Depends(get_db),
):
    """Update a session and re-sync to vector database"""
    session = db.query(models.MemorySession).filter(models.MemorySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    update_data = session_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(session, key, value)
    
    db.commit()
    db.refresh(session)
    
    # Re-sync to Weaviate
    weaviate = get_weaviate_service()
    weaviate.update_memory_session(
        str(session.id),
        session_name=session.session_name,
        summary=session.summary,
        status=session.status
    )
    
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory_session(
    session_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a memory session and remove from vector database"""
    session = db.query(models.MemorySession).filter(models.MemorySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    db.delete(session)
    db.commit()
    
    # Remove from Weaviate
    weaviate = get_weaviate_service()
    weaviate.delete_memory_session(str(session_id))
    
    return None
