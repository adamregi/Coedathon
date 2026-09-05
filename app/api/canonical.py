"""Canonical API router mounted at /api conforming strictly to the source specification."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.api.deps import (
    get_application_service,
    get_auth_service,
    get_current_user,
    get_dashboard_service,
    get_job_service,
    get_matching_service,
    get_skill_service,
    get_student_service,
    require_admin,
    require_employer_or_admin,
    require_student,
)
from app.domain.models import ApplicationStatus, Role, User
from app.schemas.application import ApplicationCreate, ApplicationRead, ApplicationStatusTransition
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRead, UserRegisterRequest
from app.schemas.envelope import ResponseEnvelope, success_envelope
from app.schemas.job import JobCreate, JobRead, JobRequirementRead, JobRequirementUpsert, JobUpdate
from app.schemas.matching import AnalysisRunRead, RecommendationRead
from app.schemas.skill import SkillCatalogCreate, SkillCatalogRead, SkillCatalogUpdate
from app.schemas.student import (
    StudentProfileCreate,
    StudentProfileRead,
    StudentProfileUpdate,
    StudentSkillCreate,
    StudentSkillRead,
)
from app.services.application_service import ApplicationService
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService
from app.services.job_service import JobService
from app.services.matching_service import MatchingService
from app.services.skill_service import SkillService
from app.services.student_service import StudentService

canonical_api_router = APIRouter()

# ---------------------------------------------------------------------------
# 1. Authentication (/api/auth)
# ---------------------------------------------------------------------------
auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post("/register", response_model=ResponseEnvelope[UserRead], status_code=status.HTTP_201_CREATED)
def register(
    req: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user. Public registration defaults to Student and blocks Admin creation."""
    user = auth_service.register_user(req)
    return success_envelope(data=user.model_dump())


@auth_router.post("/login", response_model=ResponseEnvelope[TokenResponse])
def login(
    req: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate with email and password to receive JWT access and rotating refresh tokens."""
    tokens = auth_service.login_user(req)
    return success_envelope(data=tokens.model_dump())


@auth_router.get("/me", response_model=ResponseEnvelope[UserRead])
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Retrieve the profile of the currently authenticated user."""
    return success_envelope(
        data=UserRead(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            role=current_user.role,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
        ).model_dump()
    )


# ---------------------------------------------------------------------------
# 2. Students (/api/students)
# ---------------------------------------------------------------------------
students_router = APIRouter(prefix="/students", tags=["Students"])


@students_router.get("", response_model=ResponseEnvelope[List[StudentProfileRead]])
def list_students(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    student_service: StudentService = Depends(get_student_service),
):
    """Admin only: List all student profiles."""
    skip = (page - 1) * per_page
    profiles, total = student_service.list_students(requesting_user=admin_user, skip=skip, limit=per_page)
    return success_envelope(
        data=[p.model_dump() for p in profiles],
        page=page,
        per_page=per_page,
        total=total,
    )


@students_router.post("", response_model=ResponseEnvelope[StudentProfileRead], status_code=status.HTTP_201_CREATED)
def create_student_profile(
    req: StudentProfileCreate,
    current_user: User = Depends(get_current_user),
    student_service: StudentService = Depends(get_student_service),
):
    """Create or initialize a student profile."""
    profile = student_service.get_or_create_student_by_user(current_user)
    return success_envelope(data=profile.model_dump())


@students_router.get("/{id}", response_model=ResponseEnvelope[StudentProfileRead])
def get_student(
    id: int,
    current_user: User = Depends(get_current_user),
    student_service: StudentService = Depends(get_student_service),
):
    """Get a specific student profile. Enforces Student A vs Student B isolation."""
    profile = student_service.get_student(id, requesting_user=current_user)
    return success_envelope(data=profile.model_dump())


@students_router.put("/{id}", response_model=ResponseEnvelope[StudentProfileRead])
def update_student(
    id: int,
    req: StudentProfileUpdate,
    current_user: User = Depends(get_current_user),
    student_service: StudentService = Depends(get_student_service),
):
    """Update student profile attributes. Enforces Student A vs Student B isolation."""
    updated = student_service.update_student(id, req, requesting_user=current_user)
    return success_envelope(data=updated.model_dump())


@students_router.get("/{id}/skills", response_model=ResponseEnvelope[List[StudentSkillRead]])
def get_student_skills(
    id: int,
    current_user: User = Depends(get_current_user),
    student_service: StudentService = Depends(get_student_service),
):
    """Get a student's skills. Enforces Student A vs Student B isolation."""
    skills = student_service.list_student_skills(id, requesting_user=current_user)
    return success_envelope(data=[s.model_dump() for s in skills])


@students_router.post("/{id}/skills", response_model=ResponseEnvelope[StudentSkillRead], status_code=status.HTTP_201_CREATED)
def upsert_student_skill(
    id: int,
    req: StudentSkillCreate,
    current_user: User = Depends(get_current_user),
    student_service: StudentService = Depends(get_student_service),
):
    """Add or update a skill with proficiency 1–5. Enforces Student A vs Student B isolation."""
    saved = student_service.upsert_student_skill(id, req, requesting_user=current_user)
    return success_envelope(data=saved.model_dump())


@students_router.delete("/{id}/skills/{skill_id}", response_model=ResponseEnvelope[dict])
def delete_student_skill(
    id: int,
    skill_id: int,
    current_user: User = Depends(get_current_user),
    student_service: StudentService = Depends(get_student_service),
):
    """Remove a skill from a student's profile. Enforces Student A vs Student B isolation."""
    deleted = student_service.delete_student_skill(id, skill_id, requesting_user=current_user)
    return success_envelope(data={"deleted": deleted})


# ---------------------------------------------------------------------------
# 3. Skills (/api/skills)
# ---------------------------------------------------------------------------
skills_router = APIRouter(prefix="/skills", tags=["Skills"])


@skills_router.get("", response_model=ResponseEnvelope[List[SkillCatalogRead]])
def list_skills(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by name"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    skill_service: SkillService = Depends(get_skill_service),
):
    """List skills from the global catalog."""
    skip = (page - 1) * per_page
    skills, total = skill_service.list_skills(category=category, search=search, skip=skip, limit=per_page)
    return success_envelope(
        data=[s.model_dump() for s in skills],
        page=page,
        per_page=per_page,
        total=total,
    )


@skills_router.post("", response_model=ResponseEnvelope[SkillCatalogRead], status_code=status.HTTP_201_CREATED)
def create_skill(
    req: SkillCatalogCreate,
    admin_user: User = Depends(require_admin),
    skill_service: SkillService = Depends(get_skill_service),
):
    """Admin only: Create a new normalized skill in the catalog."""
    skill = skill_service.create_skill(req, actor_id=admin_user.id)
    return success_envelope(data=skill.model_dump())


@skills_router.get("/{id}", response_model=ResponseEnvelope[SkillCatalogRead])
def get_skill(
    id: int,
    current_user: User = Depends(get_current_user),
    skill_service: SkillService = Depends(get_skill_service),
):
    """Get details for a specific catalog skill."""
    skill = skill_service.get_skill(id)
    return success_envelope(data=skill.model_dump())


@skills_router.put("/{id}", response_model=ResponseEnvelope[SkillCatalogRead])
def update_skill(
    id: int,
    req: SkillCatalogUpdate,
    admin_user: User = Depends(require_admin),
    skill_service: SkillService = Depends(get_skill_service),
):
    """Admin only: Update a skill in the catalog."""
    updated = skill_service.update_skill(id, req, actor_id=admin_user.id)
    return success_envelope(data=updated.model_dump())


@skills_router.delete("/{id}", response_model=ResponseEnvelope[dict])
def delete_skill(
    id: int,
    admin_user: User = Depends(require_admin),
    skill_service: SkillService = Depends(get_skill_service),
):
    """Admin only: Delete a skill from the catalog."""
    deleted = skill_service.delete_skill(id, actor_id=admin_user.id)
    return success_envelope(data={"deleted": deleted})


# ---------------------------------------------------------------------------
# 4. Jobs (/api/jobs)
# ---------------------------------------------------------------------------
jobs_router = APIRouter(prefix="/jobs", tags=["Jobs"])


@jobs_router.get("", response_model=ResponseEnvelope[List[JobRead]])
def list_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
):
    """List available jobs."""
    skip = (page - 1) * per_page
    jobs, total = job_service.list_jobs(search=search, skip=skip, limit=per_page)
    return success_envelope(
        data=[j.model_dump() for j in jobs],
        page=page,
        per_page=per_page,
        total=total,
    )


@jobs_router.post("", response_model=ResponseEnvelope[JobRead], status_code=status.HTTP_201_CREATED)
def create_job(
    req: JobCreate,
    current_user: User = Depends(require_employer_or_admin),
    job_service: JobService = Depends(get_job_service),
):
    """Employer / Admin: Create a new job posting."""
    job = job_service.create_job(req, employer=current_user)
    return success_envelope(data=job.model_dump())


@jobs_router.get("/{id}", response_model=ResponseEnvelope[JobRead])
def get_job(
    id: int,
    current_user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
):
    """Get details for a specific job."""
    job = job_service.get_job(id)
    return success_envelope(data=job.model_dump())


@jobs_router.put("/{id}", response_model=ResponseEnvelope[JobRead])
def update_job(
    id: int,
    req: JobUpdate,
    current_user: User = Depends(require_employer_or_admin),
    job_service: JobService = Depends(get_job_service),
):
    """Update job posting attributes."""
    updated = job_service.update_job(id, req, actor=current_user)
    return success_envelope(data=updated.model_dump())


@jobs_router.delete("/{id}", response_model=ResponseEnvelope[dict])
def delete_job(
    id: int,
    current_user: User = Depends(require_employer_or_admin),
    job_service: JobService = Depends(get_job_service),
):
    """Delete a job posting."""
    deleted = job_service.delete_job(id, actor=current_user)
    return success_envelope(data={"deleted": deleted})


@jobs_router.get("/{id}/skills", response_model=ResponseEnvelope[List[JobRequirementRead]])
def get_job_skills(
    id: int,
    current_user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
):
    """Get required skills for a job."""
    skills = job_service.get_job_skills(id)
    return success_envelope(data=[s.model_dump() for s in skills])


@jobs_router.post("/{id}/skills", response_model=ResponseEnvelope[JobRequirementRead], status_code=status.HTTP_201_CREATED)
def upsert_job_skill(
    id: int,
    req: JobRequirementUpsert,
    current_user: User = Depends(require_employer_or_admin),
    job_service: JobService = Depends(get_job_service),
):
    """Add or update a skill requirement for a job (required_level 1–5, mandatory bool)."""
    saved = job_service.upsert_job_skill(id, req, actor=current_user)
    return success_envelope(data=saved.model_dump())


@jobs_router.delete("/{id}/skills/{skill_id}", response_model=ResponseEnvelope[dict])
def delete_job_skill(
    id: int,
    skill_id: int,
    current_user: User = Depends(require_employer_or_admin),
    job_service: JobService = Depends(get_job_service),
):
    """Remove a skill requirement from a job."""
    deleted = job_service.delete_job_skill(id, skill_id, actor=current_user)
    return success_envelope(data={"deleted": deleted})


# ---------------------------------------------------------------------------
# 5. Skill Gap Analysis & Recommendations (Canonical Routes)
# ---------------------------------------------------------------------------
gap_router = APIRouter(tags=["Analysis"])


@gap_router.post("/students/{studentId}/jobs/{jobId}/skill-gap", response_model=ResponseEnvelope[AnalysisRunRead], status_code=status.HTTP_201_CREATED)
def calculate_student_job_skill_gap(
    studentId: int,
    jobId: int,
    current_user: User = Depends(get_current_user),
    matching_service: MatchingService = Depends(get_matching_service),
):
    """
    POST /api/students/{studentId}/jobs/{jobId}/skill-gap
    Calculates gaps and overall match percentage, creates immutable analysis run snapshot,
    persists individual analysis items and recommendations.
    Enforces Student A vs Student B privacy.
    """
    analysis = matching_service.calculate_and_save_analysis(studentId, jobId, actor=current_user)
    return success_envelope(data=analysis.model_dump())


@gap_router.get("/students/{studentId}/jobs/{jobId}/recommendations", response_model=ResponseEnvelope[List[RecommendationRead]])
def get_student_job_recommendations(
    studentId: int,
    jobId: int,
    current_user: User = Depends(get_current_user),
    matching_service: MatchingService = Depends(get_matching_service),
):
    """
    GET /api/students/{studentId}/jobs/{jobId}/recommendations
    Retrieves prioritized recommendations for a student and job.
    Enforces Student A vs Student B privacy.
    """
    recs = matching_service.get_recommendations_for_student_job(studentId, jobId, actor=current_user)
    return success_envelope(data=[r.model_dump() for r in recs])


# ---------------------------------------------------------------------------
# 6. Applications (/api/applications)
# ---------------------------------------------------------------------------
applications_router = APIRouter(prefix="/applications", tags=["Applications"])


@applications_router.post("", response_model=ResponseEnvelope[ApplicationRead], status_code=status.HTTP_201_CREATED)
def submit_application(
    req: ApplicationCreate,
    current_user: User = Depends(require_student),
    student_service: StudentService = Depends(get_student_service),
    application_service: ApplicationService = Depends(get_application_service),
):
    """Submit an application for a job. Captures immutable match percentage snapshot."""
    profile = student_service.get_or_create_student_by_user(current_user)
    app = application_service.submit_application(profile.id, req.job_id, student_user=current_user)
    return success_envelope(data=app.model_dump())


@applications_router.get("", response_model=ResponseEnvelope[List[ApplicationRead]])
def list_applications(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service),
):
    """List applications according to role."""
    skip = (page - 1) * per_page
    apps, total = application_service.list_applications(actor=current_user, skip=skip, limit=per_page)
    return success_envelope(
        data=[a.model_dump() for a in apps],
        page=page,
        per_page=per_page,
        total=total,
    )


@applications_router.get("/{id}", response_model=ResponseEnvelope[ApplicationRead])
def get_application(
    id: int,
    current_user: User = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service),
):
    """Get details for an application."""
    app = application_service.get_application(id, actor=current_user)
    return success_envelope(data=app.model_dump())


@applications_router.patch("/{id}/status", response_model=ResponseEnvelope[ApplicationRead])
def update_application_status(
    id: int,
    req: ApplicationStatusTransition,
    current_user: User = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service),
):
    """Update application status."""
    app = application_service.transition_status(id, req.status, actor=current_user)
    return success_envelope(data=app.model_dump())


# ---------------------------------------------------------------------------
# 7. Dashboard (/api/dashboard)
# ---------------------------------------------------------------------------
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@dashboard_router.get("", response_model=ResponseEnvelope[dict])
def get_live_dashboard(
    current_user: User = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    """
    GET /api/dashboard
    Returns dynamically computed live database aggregates (Total Students, Total Jobs,
    Total Applications, Average Skill Match, Top Skill Gaps). No hardcoded mock values.
    """
    data = dashboard_service.get_live_dashboard(actor=current_user)
    return success_envelope(data=data)


# Assemble all canonical sub-routers
canonical_api_router.include_router(auth_router)
canonical_api_router.include_router(students_router)
canonical_api_router.include_router(skills_router)
canonical_api_router.include_router(jobs_router)
canonical_api_router.include_router(gap_router)
canonical_api_router.include_router(applications_router)
canonical_api_router.include_router(dashboard_router)
