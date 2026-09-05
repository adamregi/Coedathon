from typing import List
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import (
    get_current_user,
    get_student_service,
    require_admin,
    require_student,
)
from app.domain.models import Role, User
from app.schemas.envelope import ResponseEnvelope, success_envelope
from app.schemas.student import (
    StudentProfileCreate,
    StudentProfileRead,
    StudentProfileUpdate,
    StudentSkillCreate,
    StudentSkillRead,
)
from app.services.student_service import StudentService

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/me", response_model=ResponseEnvelope[StudentProfileRead])
def get_my_profile(
    student_user: User = Depends(require_student),
    student_service: StudentService = Depends(get_student_service),
):
    """Retrieve the logged-in student's own profile and acquired skills."""
    profile = student_service.get_profile_by_user_id(student_user.id, requesting_user=student_user)
    return success_envelope(data=profile.model_dump())


@router.put("/me", response_model=ResponseEnvelope[StudentProfileRead])
def update_my_profile(
    req: StudentProfileUpdate,
    student_user: User = Depends(require_student),
    student_service: StudentService = Depends(get_student_service),
):
    """Update the logged-in student's own profile attributes."""
    updated = student_service.update_profile(student_user.id, req, requesting_user=student_user)
    return success_envelope(data=updated.model_dump())


@router.post("/me/skills", response_model=ResponseEnvelope[StudentSkillRead], status_code=status.HTTP_201_CREATED)
def upsert_my_skill(
    req: StudentSkillCreate,
    student_user: User = Depends(require_student),
    student_service: StudentService = Depends(get_student_service),
):
    """Add or update a skill with proficiency integer 1–5 on the student's profile."""
    saved = student_service.upsert_student_skill(student_user.id, req, requesting_user=student_user)
    return success_envelope(data=saved.model_dump())


@router.delete("/me/skills/{skill_id}", response_model=ResponseEnvelope[dict])
def delete_my_skill(
    skill_id: int,
    student_user: User = Depends(require_student),
    student_service: StudentService = Depends(get_student_service),
):
    """Remove a skill from the logged-in student's profile."""
    deleted = student_service.delete_student_skill(student_user.id, skill_id, requesting_user=student_user)
    return success_envelope(data={"deleted": deleted})


@router.get("", response_model=ResponseEnvelope[List[StudentProfileRead]])
def list_student_profiles(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    student_service: StudentService = Depends(get_student_service),
):
    """Admin only: List all student profiles in the platform."""
    skip = (page - 1) * per_page
    profiles, total = student_service.list_profiles(requesting_user=admin_user, skip=skip, limit=per_page)
    return success_envelope(
        data=[p.model_dump() for p in profiles],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/{user_id}", response_model=ResponseEnvelope[StudentProfileRead])
def get_student_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    student_service: StudentService = Depends(get_student_service),
):
    """Retrieve a specific student profile. Students can only inspect themselves; admins have global view."""
    profile = student_service.get_profile_by_user_id(user_id, requesting_user=current_user)
    return success_envelope(data=profile.model_dump())
