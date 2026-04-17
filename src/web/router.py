"""
BrainCell Web Dashboard Router

Provides web UI for viewing BrainCell memory data (conversations, decisions, notes, snippets).
"""
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pathlib import Path
from datetime import datetime, timedelta

from src.core.database import get_db
from src.cells.conversations.model import Conversation
from src.cells.decisions.model import DesignDecision
from src.cells.architecture_notes.model import ArchitectureNote
from src.cells.snippets.model import CodeSnippet
from src.cells.interactions.model import Interaction
from src.cells.files_discussed.model import FileDiscussed

# Setup
web_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(web_dir / "templates"))
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page with overview statistics and recent items"""
    
    # Get statistics
    total_conversations = db.query(func.count(Conversation.id)).scalar() or 0
    total_decisions = db.query(func.count(DesignDecision.id)).scalar() or 0
    total_notes = db.query(func.count(ArchitectureNote.id)).scalar() or 0
    total_snippets = db.query(func.count(CodeSnippet.id)).scalar() or 0
    total_interactions = db.query(func.count(Interaction.id)).scalar() or 0
    
    # Get recent items
    recent_conversations = (
        db.query(Conversation)
        .order_by(desc(Conversation.created_at))
        .limit(5)
        .all()
    )
    
    recent_decisions = (
        db.query(DesignDecision)
        .order_by(desc(DesignDecision.created_at))
        .limit(5)
        .all()
    )
    
    recent_notes = (
        db.query(ArchitectureNote)
        .order_by(desc(ArchitectureNote.created_at))
        .limit(5)
        .all()
    )
    
    recent_snippets = (
        db.query(CodeSnippet)
        .order_by(desc(CodeSnippet.created_at))
        .limit(5)
        .all()
    )
    
    stats = {
        "conversations": total_conversations,
        "decisions": total_decisions,
        "notes": total_notes,
        "snippets": total_snippets,
        "interactions": total_interactions,
    }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_conversations": recent_conversations,
        "recent_decisions": recent_decisions,
        "recent_notes": recent_notes,
        "recent_snippets": recent_snippets,
    })


@router.get("/conversations", response_class=HTMLResponse)
async def conversations_list(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = Query(0),
    limit: int = Query(20),
):
    """List all conversations"""
    
    total = db.query(func.count(Conversation.id)).scalar() or 0
    conversations = (
        db.query(Conversation)
        .order_by(desc(Conversation.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return templates.TemplateResponse("conversations.html", {
        "request": request,
        "conversations": conversations,
        "total": total,
        "skip": skip,
        "limit": limit,
    })


@router.get("/decisions", response_class=HTMLResponse)
async def decisions_list(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = Query(0),
    limit: int = Query(20),
):
    """List all design decisions"""
    
    total = db.query(func.count(DesignDecision.id)).scalar() or 0
    decisions = (
        db.query(DesignDecision)
        .order_by(desc(DesignDecision.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return templates.TemplateResponse("decisions.html", {
        "request": request,
        "decisions": decisions,
        "total": total,
        "skip": skip,
        "limit": limit,
    })


@router.get("/architecture-notes", response_class=HTMLResponse)
async def architecture_notes_list(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = Query(0),
    limit: int = Query(20),
):
    """List all architecture notes"""
    
    total = db.query(func.count(ArchitectureNote.id)).scalar() or 0
    notes = (
        db.query(ArchitectureNote)
        .order_by(desc(ArchitectureNote.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return templates.TemplateResponse("architecture_notes.html", {
        "request": request,
        "notes": notes,
        "total": total,
        "skip": skip,
        "limit": limit,
    })


@router.get("/code-snippets", response_class=HTMLResponse)
async def code_snippets_list(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = Query(0),
    limit: int = Query(20),
):
    """List all code snippets"""
    
    total = db.query(func.count(CodeSnippet.id)).scalar() or 0
    snippets = (
        db.query(CodeSnippet)
        .order_by(desc(CodeSnippet.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return templates.TemplateResponse("code_snippets.html", {
        "request": request,
        "snippets": snippets,
        "total": total,
        "skip": skip,
        "limit": limit,
    })


@router.get("/search", response_class=HTMLResponse)
async def search_memory(
    request: Request,
    q: str = Query(""),
    db: Session = Depends(get_db),
):
    """Search across all memory types"""
    
    results = {
        "conversations": [],
        "decisions": [],
        "notes": [],
        "snippets": [],
    }
    
    if len(q) > 2:
        search_term = f"%{q}%"
        
        results["conversations"] = (
            db.query(Conversation)
            .filter(Conversation.topic.ilike(search_term))
            .limit(5)
            .all()
        )
        
        results["decisions"] = (
            db.query(DesignDecision)
            .filter(DesignDecision.decision.ilike(search_term))
            .limit(5)
            .all()
        )
        
        results["notes"] = (
            db.query(ArchitectureNote)
            .filter(ArchitectureNote.description.ilike(search_term))
            .limit(5)
            .all()
        )
        
        results["snippets"] = (
            db.query(CodeSnippet)
            .filter(CodeSnippet.code_content.ilike(search_term))
            .limit(5)
            .all()
        )
    
    return templates.TemplateResponse("search.html", {
        "request": request,
        "query": q,
        "results": results,
    })
