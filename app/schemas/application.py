from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.domain.models import ApplicationStatus


class ApplicationCreate(BaseModel):
    job_id: int


class ApplicationStatusTransition(BaseModel):
    status: ApplicationStatus


class ApplicationRead(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    job_id: int
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    status: ApplicationStatus
    match_percentage_snapshot: int
    created_at: datetime
    updated_at: datetime
