"""Jobs routes for storing and searching job postings."""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.schemas import SearchQuery, SearchResult
from src.services.weaviate_service import get_weaviate_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


# ============================================================================
# Pydantic Models
# ============================================================================

class JobInput(BaseModel):
    """Input model for storing a job."""
    
    job_id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    job_type: Optional[str] = None
    seniority_level: Optional[str] = None
    posted_date: Optional[str] = None
    tags: Optional[List[str]] = None


class BatchJobInput(BaseModel):
    """Batch input for storing multiple jobs."""
    
    jobs: List[JobInput]


class JobSearchQuery(BaseModel):
    """Search query for jobs."""
    
    query: str
    limit: int = 50
    source: Optional[str] = None
    job_type: Optional[str] = None
    location: Optional[str] = None


# ============================================================================
# Routes
# ============================================================================

@router.post("/", status_code=201)
async def store_job(
    job: JobInput,
    db: Session = Depends(get_db),
):
    """Store a single job in Weaviate vector DB."""
    try:
        weaviate = get_weaviate_service()
        
        success = weaviate.index_job(
            job_id=job.job_id,
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            url=job.url,
            source=job.source,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            job_type=job.job_type,
            seniority_level=job.seniority_level,
            posted_date=job.posted_date,
            tags=job.tags
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Job stored: {job.job_id}",
                "job_id": job.job_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to store job")
    
    except Exception as e:
        logger.error(f"Error storing job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", status_code=201)
async def store_jobs_batch(
    batch: BatchJobInput,
    db: Session = Depends(get_db),
):
    """Store multiple jobs in batch."""
    try:
        weaviate = get_weaviate_service()
        
        successful = 0
        failed = 0
        errors = []
        
        for job in batch.jobs:
            try:
                success = weaviate.index_job(
                    job_id=job.job_id,
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    description=job.description,
                    url=job.url,
                    source=job.source,
                    salary_min=job.salary_min,
                    salary_max=job.salary_max,
                    job_type=job.job_type,
                    seniority_level=job.seniority_level,
                    posted_date=job.posted_date,
                    tags=job.tags
                )
                
                if success:
                    successful += 1
                else:
                    failed += 1
                    errors.append(f"Failed to store job: {job.job_id}")
            
            except Exception as e:
                failed += 1
                errors.append(f"Error storing {job.job_id}: {str(e)}")
        
        return {
            "status": "success",
            "successful": successful,
            "failed": failed,
            "total": len(batch.jobs),
            "errors": errors
        }
    
    except Exception as e:
        logger.error(f"Error in batch job storage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=list[SearchResult])
async def search_jobs(
    search_query: JobSearchQuery,
    db: Session = Depends(get_db),
):
    """Search jobs using semantic similarity."""
    try:
        weaviate = get_weaviate_service()
        
        results = weaviate.search_jobs(
            query=search_query.query,
            limit=search_query.limit,
            source=search_query.source,
            job_type=search_query.job_type,
            location=search_query.location
        )
        
        return [
            SearchResult(
                id=UUID(r.get("job_id", r.get("uuid", ""))),
                type="job",
                title=r.get("title", ""),
                content=r.get("description", ""),
                similarity_score=1 - r.get("_additional", {}).get("distance", 1),
                metadata={
                    "company": r.get("company", ""),
                    "location": r.get("location", ""),
                    "source": r.get("source", ""),
                    "job_type": r.get("job_type", ""),
                    "salary_min": r.get("salary_min"),
                    "salary_max": r.get("salary_max"),
                    "url": r.get("url", ""),
                    "posted_date": r.get("posted_date", ""),
                }
            )
            for r in results if r.get("job_id") or r.get("uuid")
        ]
    
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific job by ID."""
    try:
        weaviate = get_weaviate_service()
        
        # Search for the job
        results = weaviate.search_jobs(
            query=f"job id {job_id}",
            limit=1
        )
        
        if results:
            job = results[0]
            return {
                "status": "success",
                "job": job
            }
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    
    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    """Delete a job by ID."""
    try:
        weaviate = get_weaviate_service()
        
        success = weaviate.delete_job(job_id)
        
        if success:
            return {"status": "success", "message": f"Job deleted: {job_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete job")
    
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{job_id}", status_code=200)
async def update_job(
    job_id: str,
    updates: dict,
    db: Session = Depends(get_db),
):
    """Update a job (re-index with new data)."""
    try:
        weaviate = get_weaviate_service()
        
        # For update, we delete the old and insert the new
        weaviate.delete_job(job_id)
        
        success = weaviate.index_job(
            job_id=updates.get("job_id", job_id),
            title=updates.get("title", ""),
            company=updates.get("company", ""),
            location=updates.get("location", ""),
            description=updates.get("description", ""),
            url=updates.get("url", ""),
            source=updates.get("source", ""),
            salary_min=updates.get("salary_min"),
            salary_max=updates.get("salary_max"),
            job_type=updates.get("job_type"),
            seniority_level=updates.get("seniority_level"),
            posted_date=updates.get("posted_date"),
            tags=updates.get("tags")
        )
        
        if success:
            return {"status": "success", "message": f"Job updated: {job_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update job")
    
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
