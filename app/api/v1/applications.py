from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import (
    get_application_service,
    get_current_user,
    require_student,
)
from app.domain.models import ApplicationStatus, User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationStatusTransition,
)
from app.schemas.envelope import ResponseEnvelope, success_envelope
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=ResponseEnvelope[ApplicationRead], status_code=status.HTTP_201_CREATED)
def submit_application(
    req: ApplicationCreate,
    student_user: User = Depends(require_student),
    application_service: ApplicationService = Depends(get_application_service),
):
    """
    Student submits an application for a job.
    Captures an immutable match percentage snapshot at the exact moment of application.
    Rejects duplicate active applications for the same student/job.
    """
    created = application_service.submit_application(
        student_id=student_user.id,
        job_id=req.job_id,
        student_user=student_user,
    )
    return success_envelope(data=created.model_dump())


@router.post("/{application_id}/withdraw", response_model=ResponseEnvelope[ApplicationRead])
def withdraw_application(
    application_id: int,
    student_user: User = Depends(require_student),
    application_service: ApplicationService = Depends(get_application_service),
):
    """Student withdraws their own active application."""
    updated = application_service.withdraw_application(
        application_id=application_id,
        student_user=student_user,
    )
    return success_envelope(data=updated.model_dump())


@router.patch("/{application_id}/status", response_model=ResponseEnvelope[ApplicationRead])
def transition_application_status(
    application_id: int,
    req: ApplicationStatusTransition,
    current_user: User = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service),
):
    """
    Employer / Admin: Advance application state through the strict finite state machine:
    submitted -> reviewed -> shortlisted | rejected -> closed.
    Rejects invalid state transitions.
    """
    updated = application_service.transition_status(
        application_id=application_id,
        new_status=req.status,
        actor=current_user,
    )
    return success_envelope(data=updated.model_dump())


@router.get("", response_model=ResponseEnvelope[List[ApplicationRead]])
def list_applications(
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    status: Optional[ApplicationStatus] = Query(None, description="Filter by application status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service),
):
    """
    List applications. Students see only their applications; employers see applications for their jobs;
    admins see global list.
    """
    skip = (page - 1) * per_page
    apps, total = application_service.list_applications(
        actor=current_user,
        job_id=job_id,
        status=status,
        skip=skip,
        limit=per_page,
    )
    return success_envelope(
        data=[a.model_dump() for a in apps],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/{application_id}", response_model=ResponseEnvelope[ApplicationRead])
def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service),
):
    """Retrieve details for a specific application with permission enforcement."""
    app_read = application_service.get_application(application_id, actor=current_user)
    return success_envelope(data=app_read.model_dump())
