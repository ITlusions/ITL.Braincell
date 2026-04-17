"""Architecture Notes entity routes - document system architecture and design patterns"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core import models
from src.core.database import get_db
from src.core.schemas import ArchitectureNoteCreate, ArchitectureNoteResponse
from src.services.weaviate_service import get_weaviate_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ArchitectureNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_architecture_note(
    note: ArchitectureNoteCreate,
    db: Session = Depends(get_db),
):
    """Create an architecture note and sync to vector database"""
    db_note = models.ArchitectureNote(**note.model_dump())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    
    # Sync to Weaviate vector database
    weaviate = get_weaviate_service()
    success = weaviate.index_architecture_note(
        str(db_note.id),
        db_note.component,
        db_note.description,
        db_note.type,
        db_note.tags
    )
    
    if not success:
        logger.warning(f"Failed to sync architecture note {db_note.id} to Weaviate")
    
    return db_note


@router.get("", response_model=list[ArchitectureNoteResponse])
async def get_architecture_notes(
    component: str = None,
    db: Session = Depends(get_db),
):
    """Get all architecture notes, optionally filtered by component"""
    query = db.query(models.ArchitectureNote)
    if component:
        query = query.filter(models.ArchitectureNote.component.contains(component))
    return query.order_by(models.ArchitectureNote.updated_at.desc()).all()


@router.put("/{note_id}", response_model=ArchitectureNoteResponse)
async def update_architecture_note(
    note_id: UUID,
    note_update: ArchitectureNoteCreate,
    db: Session = Depends(get_db),
):
    """Update an architecture note and re-sync to vector database"""
    note = db.query(models.ArchitectureNote).filter(models.ArchitectureNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Architecture note not found")
    
    for key, value in note_update.model_dump(exclude_unset=True).items():
        setattr(note, key, value)
    
    db.commit()
    db.refresh(note)
    
    # Re-sync to Weaviate
    weaviate = get_weaviate_service()
    weaviate.update_architecture_note(
        str(note.id),
        component=note.component,
        description=note.description,
        note_type=note.type
    )
    
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_architecture_note(
    note_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete an architecture note and remove from vector database"""
    note = db.query(models.ArchitectureNote).filter(models.ArchitectureNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Architecture note not found")
    
    db.delete(note)
    db.commit()
    
    # Remove from Weaviate
    weaviate = get_weaviate_service()
    weaviate.delete_architecture_note(str(note_id))
    
    return None
