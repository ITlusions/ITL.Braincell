"""Conversation entity routes - CRUD operations with vector sync"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core import models
from src.core.database import get_db
from src.core.schemas import ConversationCreate, ConversationResponse, ConversationUpdate
from src.services.weaviate_service import get_weaviate_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conv: ConversationCreate,
    db: Session = Depends(get_db),
):
    """Create a new conversation and sync to vector database"""
    db_conv = models.Conversation(**conv.model_dump())
    db.add(db_conv)
    db.commit()
    db.refresh(db_conv)
    
    # Sync to Weaviate vector database
    weaviate = get_weaviate_service()
    success = weaviate.index_conversation(
        str(db_conv.id),
        db_conv.topic,
        db_conv.summary,
        str(db_conv.session_id)
    )
    
    if not success:
        logger.warning(f"Failed to sync conversation {db_conv.id} to Weaviate")
    
    return db_conv


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a conversation by ID"""
    conv = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    conv_update: ConversationUpdate,
    db: Session = Depends(get_db),
):
    """Update a conversation and re-sync to vector database"""
    conv = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    update_data = conv_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(conv, key, value)
    
    db.commit()
    db.refresh(conv)
    
    # Sync update to Weaviate
    weaviate = get_weaviate_service()
    weaviate.update_conversation(
        str(conv.id),
        topic=conv.topic,
        summary=conv.summary
    )
    
    return conv


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a conversation and remove from vector database"""
    conv = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    db.delete(conv)
    db.commit()
    
    # Remove from Weaviate
    weaviate = get_weaviate_service()
    weaviate.delete_conversation(str(conversation_id))
    
    return None
