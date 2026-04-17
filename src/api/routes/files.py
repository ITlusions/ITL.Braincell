"""Files Discussed entity routes - track and document files discussed in conversations"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core import models
from src.core.database import get_db
from src.core.schemas import FileDiscussedCreate, FileDiscussedResponse
from src.services.weaviate_service import get_weaviate_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=FileDiscussedResponse, status_code=status.HTTP_201_CREATED)
async def create_file_discussed(
    file: FileDiscussedCreate,
    db: Session = Depends(get_db),
):
    """Record a file discussion and sync to vector database"""
    db_file = db.query(models.FileDiscussed).filter(
        models.FileDiscussed.file_path == file.file_path
    ).first()
    
    if db_file:
        # File already exists - increment discussion counter
        db_file.discussion_count += 1
        db.commit()
        db.refresh(db_file)
        return db_file
    
    # Create new file record
    db_file = models.FileDiscussed(**file.model_dump())
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    # Sync to Weaviate vector database
    weaviate = get_weaviate_service()
    success = weaviate.index_file_discussed(
        str(db_file.id),
        db_file.file_path,
        db_file.description,
        db_file.language,
        db_file.purpose
    )
    
    if not success:
        logger.warning(f"Failed to sync file {db_file.id} to Weaviate")
    
    return db_file


@router.get("", response_model=list[FileDiscussedResponse])
async def get_discussed_files(
    language: str = None,
    db: Session = Depends(get_db),
):
    """Get all discussed files, optionally filtered by language"""
    query = db.query(models.FileDiscussed)
    if language:
        query = query.filter(models.FileDiscussed.language == language)
    return query.order_by(models.FileDiscussed.discussion_count.desc()).all()


@router.put("/{file_id}", response_model=FileDiscussedResponse)
async def update_file_discussed(
    file_id: UUID,
    file_update: FileDiscussedCreate,
    db: Session = Depends(get_db),
):
    """Update a file discussion record and re-sync to vector database"""
    file = db.query(models.FileDiscussed).filter(models.FileDiscussed.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    for key, value in file_update.model_dump(exclude_unset=True).items():
        setattr(file, key, value)
    
    db.commit()
    db.refresh(file)
    
    # Re-sync to Weaviate
    weaviate = get_weaviate_service()
    weaviate.update_file_discussed(
        str(file.id),
        description=file.description,
        purpose=file.purpose
    )
    
    return file


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_discussed(
    file_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a file discussion record and remove from vector database"""
    file = db.query(models.FileDiscussed).filter(models.FileDiscussed.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    db.delete(file)
    db.commit()
    
    # Remove from Weaviate
    weaviate = get_weaviate_service()
    weaviate.delete_file_discussed(str(file_id))
    
    return None
