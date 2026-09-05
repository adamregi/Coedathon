from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import (
    get_current_user,
    get_job_service,
    require_employer_or_admin,
)
from app.domain.models import User
from app.schemas.envelope import ResponseEnvelope, success_envelope
from app.schemas.job import (
    JobCreate,
    JobRead,
    JobRequirementRead,
    JobRequirementUpsert,
    JobUpdate,
)
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=ResponseEnvelope[JobRead], status_code=status.HTTP_201_CREATED)
def create_job(
    req: JobCreate,
    current_user: User = Depends(require_employer_or_admin),
    job_service: JobService = Depends(get_job_service),
):
    """Employer / Admin: Create a new job posting with optional initial requirements."""
    job = job_service.create_job(req, employer=current_user)
    return success_envelope(data=job.model_dump())


@router.get("", response_model=ResponseEnvelope[List[JobRead]])
def list_jobs(
    employer_id: Optional[int] = Query(None, description="Filter by posting employer ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search job title, company, or description"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
):
    """Browse jobs with optional filters, keyword search, and pagination."""
    skip = (page - 1) * per_page
    jobs, total = job_service.list_jobs(
        employer_id=employer_id,
        is_active=is_active,
        search=search,
        skip=skip,
        limit=per_page,
    )
    return success_envelope(
        data=[j.model_dump() for j in jobs],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/{job_id}", response_model=ResponseEnvelope[JobRead])
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
):
    """Retrieve details and requirements for a specific job."""
    job = job_service.get_job(job_id)
    return success_envelope(data=job.model_dump())


@router.put("/{job_id}", response_model=ResponseEnvelope[JobRead])
def update_job(
    job_id: int,
    req: JobUpdate,
    current_user: User = Depends(require_employer_or_admin),
    job_service: JobService = Depends(get_job_service),
):
    """Update job attributes. Employers can only update their own jobs."""
    updated = job_service.update_job(job_id, req, actor=current_user)
    return success_envelope(data=updated.model_dump())


@router.delete("/{job_id}", response_model=ResponseEnvelope[dict])
def delete_job(
    job_id: int,
    current_user: User = Depends(require_employer_or_admin),
    job_service: JobService = Depends(get_job_service),
):
    """Delete a job posting. Employers can only delete their own jobs."""
    deleted = job_service.delete_job(job_id, actor=current_user)
    return success_envelope(data={"deleted": deleted})


@router.post("/{job_id}/requirements", response_model=ResponseEnvelope[JobRequirementRead], status_code=status.HTTP_201_CREATED)
def upsert_job_requirement(
    job_id: int,
    req: JobRequirementUpsert,
    current_user: User = Depends(require_employer_or_admin),
    job_service: JobService = Depends(get_job_service),
):
    """Add or update a requirement for a job. Enforces proficiency 1–5 and mandatory weight flag."""
    saved = job_service.upsert_requirement(job_id, req, actor=current_user)
    return success_envelope(data=saved.model_dump())


@router.delete("/{job_id}/requirements/{skill_id}", response_model=ResponseEnvelope[dict])
def delete_job_requirement(
    job_id: int,
    skill_id: int,
    current_user: User = Depends(require_employer_or_admin),
    job_service: JobService = Depends(get_job_service),
):
    """Remove a skill requirement from a job posting."""
    deleted = job_service.delete_requirement(job_id, skill_id, actor=current_user)
    return success_envelope(data={"deleted": deleted})
