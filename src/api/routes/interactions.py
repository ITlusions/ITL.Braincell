"""Interaction/Message entity routes - track individual conversation messages"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core import models
from src.core.database import get_db
from src.core.schemas import InteractionCreate, InteractionResponse, InteractionUpdate
from src.services.weaviate_service import get_weaviate_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
async def create_interaction(
    interaction: InteractionCreate,
    db: Session = Depends(get_db),
):
    """Create a new interaction/message and sync to vector database"""
    db_interaction = models.Interaction(**interaction.model_dump())
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    
    # Sync to Weaviate vector database for semantic search
    weaviate = get_weaviate_service()
    success = weaviate.index_interaction(
        str(db_interaction.id),
        db_interaction.content,
        db_interaction.role,
        db_interaction.message_type,
        str(db_interaction.conversation_id),
        str(db_interaction.session_id)
    )
    
    if not success:
        logger.warning(f"Failed to sync interaction {db_interaction.id} to Weaviate")
    
    return db_interaction


@router.get("/{interaction_id}", response_model=InteractionResponse)
async def get_interaction(
    interaction_id: UUID,
    db: Session = Depends(get_db),
):
    """Get an interaction by ID"""
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")
    return interaction


@router.get("/conversations/{conversation_id}", response_model=list[InteractionResponse])
async def get_conversation_interactions(
    conversation_id: UUID,
    db: Session = Depends(get_db),
):
    """Get all interactions for a specific conversation"""
    interactions = db.query(models.Interaction).filter(
        models.Interaction.conversation_id == conversation_id
    ).order_by(models.Interaction.timestamp.asc()).all()
    return interactions


@router.put("/{interaction_id}", response_model=InteractionResponse)
async def update_interaction(
    interaction_id: UUID,
    interaction_update: InteractionUpdate,
    db: Session = Depends(get_db),
):
    """Update an interaction and re-sync to vector database"""
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")
    
    update_data = interaction_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(interaction, key, value)
    
    db.commit()
    db.refresh(interaction)
    
    # Sync update to Weaviate
    weaviate = get_weaviate_service()
    weaviate.update_interaction(
        str(interaction.id),
        content=interaction.content,
        role=interaction.role,
        message_type=interaction.message_type
    )
    
    return interaction


@router.delete("/{interaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interaction(
    interaction_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete an interaction and remove from vector database"""
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")
    
    db.delete(interaction)
    db.commit()
    
    # Remove from Weaviate
    weaviate = get_weaviate_service()
    weaviate.delete_interaction(str(interaction_id))
    
    return None
