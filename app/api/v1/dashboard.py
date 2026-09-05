from fastapi import APIRouter, Depends
from app.api.deps import (
    get_dashboard_service,
    require_admin,
    require_employer_or_admin,
    require_student,
)
from app.domain.models import User
from app.schemas.dashboard import (
    AdminDashboardRead,
    EmployerDashboardRead,
    StudentDashboardRead,
)
from app.schemas.envelope import ResponseEnvelope, success_envelope
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/student", response_model=ResponseEnvelope[StudentDashboardRead])
def get_student_dashboard(
    student_user: User = Depends(require_student),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    """Retrieve personal metrics, match averages, active applications, and skill gap priorities."""
    stats = dashboard_service.get_student_dashboard(student_user)
    return success_envelope(data=stats.model_dump())


@router.get("/employer", response_model=ResponseEnvelope[EmployerDashboardRead])
def get_employer_dashboard(
    employer_user: User = Depends(require_employer_or_admin),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    """Retrieve employer pipeline metrics: active jobs, candidate averages, and applicant skill gaps."""
    stats = dashboard_service.get_employer_dashboard(employer_user)
    return success_envelope(data=stats.model_dump())


@router.get("/admin", response_model=ResponseEnvelope[AdminDashboardRead])
def get_admin_dashboard(
    admin_user: User = Depends(require_admin),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    """Admin only: System-wide aggregated analytics, user breakdowns, and in-demand skills."""
    stats = dashboard_service.get_admin_dashboard(admin_user)
    return success_envelope(data=stats.model_dump())
