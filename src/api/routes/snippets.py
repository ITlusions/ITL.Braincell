"""Code Snippets entity routes - store and search reusable code samples"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core import models
from src.core.database import get_db
from src.core.schemas import CodeSnippetCreate, CodeSnippetResponse
from src.services.weaviate_service import get_weaviate_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=CodeSnippetResponse, status_code=status.HTTP_201_CREATED)
async def create_code_snippet(
    snippet: CodeSnippetCreate,
    db: Session = Depends(get_db),
):
    """Create a code snippet and sync to vector database"""
    db_snippet = models.CodeSnippet(**snippet.model_dump())
    db.add(db_snippet)
    db.commit()
    db.refresh(db_snippet)
    
    # Sync to Weaviate vector database
    weaviate = get_weaviate_service()
    success = weaviate.index_code_snippet(
        str(db_snippet.id),
        db_snippet.title,
        db_snippet.code_content,
        db_snippet.language
    )
    
    if not success:
        logger.warning(f"Failed to sync code snippet {db_snippet.id} to Weaviate")
    
    return db_snippet


@router.get("", response_model=list[CodeSnippetResponse])
async def get_code_snippets(
    language: str = None,
    db: Session = Depends(get_db),
):
    """Get code snippets, optionally filtered by language"""
    query = db.query(models.CodeSnippet)
    if language:
        query = query.filter(models.CodeSnippet.language == language)
    return query.order_by(models.CodeSnippet.created_at.desc()).all()


@router.put("/{snippet_id}", response_model=CodeSnippetResponse)
async def update_code_snippet(
    snippet_id: UUID,
    snippet_update: CodeSnippetCreate,
    db: Session = Depends(get_db),
):
    """Update a code snippet and re-sync to vector database"""
    snippet = db.query(models.CodeSnippet).filter(models.CodeSnippet.id == snippet_id).first()
    if not snippet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Code snippet not found")
    
    for key, value in snippet_update.model_dump(exclude_unset=True).items():
        setattr(snippet, key, value)
    
    db.commit()
    db.refresh(snippet)
    
    # Re-sync to Weaviate
    weaviate = get_weaviate_service()
    weaviate.index_code_snippet(
        str(snippet.id),
        snippet.title,
        snippet.code_content,
        snippet.language
    )
    
    return snippet


@router.delete("/{snippet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_code_snippet(
    snippet_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a code snippet and remove from vector database"""
    snippet = db.query(models.CodeSnippet).filter(models.CodeSnippet.id == snippet_id).first()
    if not snippet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Code snippet not found")
    
    db.delete(snippet)
    db.commit()
    
    # Remove from Weaviate
    weaviate = get_weaviate_service()
    weaviate.delete_code_snippet(str(snippet_id))
    
    return None
