from typing import List, Optional, Tuple
from app.core.audit import emit_audit_event
from app.core.errors import ResourceConflictException, ResourceNotFoundException
from app.domain.models import SkillCatalog
from app.domain.protocols import SkillRepositoryProtocol
from app.schemas.skill import SkillCatalogCreate, SkillCatalogRead, SkillCatalogUpdate, normalize_skill_name


class SkillService:
    def __init__(self, skill_repo: SkillRepositoryProtocol):
        self.skill_repo = skill_repo

    def create_skill(self, req: SkillCatalogCreate, actor_id: int) -> SkillCatalogRead:
        normalized = normalize_skill_name(req.name)
        existing = self.skill_repo.get_by_normalized_name(normalized)
        if existing:
            raise ResourceConflictException(f"Skill with name '{normalized}' already exists")

        skill = SkillCatalog(
            id=0,
            name=normalized,
            normalized_name=normalized,
            category=req.category,
            description=req.description,
        )
        created = self.skill_repo.create(skill)

        emit_audit_event(
            action="SKILL_CREATED",
            actor_id=actor_id,
            actor_role="admin",
            target_type="skill",
            target_id=str(created.id),
            details={"name": created.name, "category": created.category},
        )

        return SkillCatalogRead(
            id=created.id,
            name=created.name,
            normalized_name=created.normalized_name,
            category=created.category,
            description=created.description,
            created_at=created.created_at,
            updated_at=created.updated_at,
        )

    def get_skill(self, skill_id: int) -> SkillCatalogRead:
        skill = self.skill_repo.get_by_id(skill_id)
        if not skill:
            raise ResourceNotFoundException(f"Skill with ID {skill_id} not found")
        return SkillCatalogRead(
            id=skill.id,
            name=skill.name,
            normalized_name=skill.normalized_name,
            category=skill.category,
            description=skill.description,
            created_at=skill.created_at,
            updated_at=skill.updated_at,
        )

    def update_skill(self, skill_id: int, req: SkillCatalogUpdate, actor_id: int) -> SkillCatalogRead:
        skill = self.skill_repo.get_by_id(skill_id)
        if not skill:
            raise ResourceNotFoundException(f"Skill with ID {skill_id} not found")

        if req.name is not None:
            normalized = normalize_skill_name(req.name)
            existing = self.skill_repo.get_by_normalized_name(normalized)
            if existing and existing.id != skill_id:
                raise ResourceConflictException(f"Another skill with name '{normalized}' already exists")
            skill.name = normalized
            skill.normalized_name = normalized

        if req.category is not None:
            skill.category = req.category

        if req.description is not None:
            skill.description = req.description

        updated = self.skill_repo.update(skill)

        emit_audit_event(
            action="SKILL_UPDATED",
            actor_id=actor_id,
            actor_role="admin",
            target_type="skill",
            target_id=str(updated.id),
            details={"name": updated.name, "category": updated.category},
        )

        return SkillCatalogRead(
            id=updated.id,
            name=updated.name,
            normalized_name=updated.normalized_name,
            category=updated.category,
            description=updated.description,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )

    def delete_skill(self, skill_id: int, actor_id: int) -> bool:
        skill = self.skill_repo.get_by_id(skill_id)
        if not skill:
            raise ResourceNotFoundException(f"Skill with ID {skill_id} not found")

        success = self.skill_repo.delete(skill_id)
        emit_audit_event(
            action="SKILL_DELETED",
            actor_id=actor_id,
            actor_role="admin",
            target_type="skill",
            target_id=str(skill_id),
            details={"name": skill.name},
        )
        return success

    def list_skills(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[SkillCatalogRead], int]:
        skills, total = self.skill_repo.list_all(category=category, search=search, skip=skip, limit=limit)
        return [
            SkillCatalogRead(
                id=s.id,
                name=s.name,
                normalized_name=s.normalized_name,
                category=s.category,
                description=s.description,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in skills
        ], total
