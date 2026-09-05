from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_current_user, get_skill_service, require_admin
from app.domain.models import User
from app.schemas.envelope import ResponseEnvelope, success_envelope
from app.schemas.skill import SkillCatalogCreate, SkillCatalogRead, SkillCatalogUpdate
from app.services.skill_service import SkillService

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.post("", response_model=ResponseEnvelope[SkillCatalogRead], status_code=status.HTTP_201_CREATED)
def create_skill(
    req: SkillCatalogCreate,
    admin_user: User = Depends(require_admin),
    skill_service: SkillService = Depends(get_skill_service),
):
    """Admin only: Add a new normalized skill to the global catalog."""
    created = skill_service.create_skill(req, actor_id=admin_user.id)
    return success_envelope(data=created.model_dump())


@router.get("", response_model=ResponseEnvelope[List[SkillCatalogRead]])
def list_skills(
    category: Optional[str] = Query(None, description="Filter by skill category"),
    search: Optional[str] = Query(None, description="Search skill name or description"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    skill_service: SkillService = Depends(get_skill_service),
    current_user: User = Depends(get_current_user),
):
    """List skills from the catalog with optional category filtering and search."""
    skip = (page - 1) * per_page
    skills, total = skill_service.list_skills(category=category, search=search, skip=skip, limit=per_page)
    return success_envelope(
        data=[s.model_dump() for s in skills],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/{skill_id}", response_model=ResponseEnvelope[SkillCatalogRead])
def get_skill(
    skill_id: int,
    skill_service: SkillService = Depends(get_skill_service),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details for a specific skill from the catalog."""
    skill = skill_service.get_skill(skill_id)
    return success_envelope(data=skill.model_dump())


@router.put("/{skill_id}", response_model=ResponseEnvelope[SkillCatalogRead])
def update_skill(
    skill_id: int,
    req: SkillCatalogUpdate,
    admin_user: User = Depends(require_admin),
    skill_service: SkillService = Depends(get_skill_service),
):
    """Admin only: Update a skill's name, category, or description."""
    updated = skill_service.update_skill(skill_id, req, actor_id=admin_user.id)
    return success_envelope(data=updated.model_dump())


@router.delete("/{skill_id}", response_model=ResponseEnvelope[dict])
def delete_skill(
    skill_id: int,
    admin_user: User = Depends(require_admin),
    skill_service: SkillService = Depends(get_skill_service),
):
    """Admin only: Remove a skill from the catalog."""
    deleted = skill_service.delete_skill(skill_id, actor_id=admin_user.id)
    return success_envelope(data={"deleted": deleted})
