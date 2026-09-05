from typing import Any, List, Optional, Tuple
from app.core.audit import emit_audit_event
from app.core.errors import (
    PermissionDeniedException,
    ResourceConflictException,
    ResourceNotFoundException,
    ValidationException,
)
from app.domain.models import Role, SkillCatalog, StudentProfile, StudentSkill, User
from app.domain.protocols import SkillRepositoryProtocol, StudentRepositoryProtocol, UserRepositoryProtocol
from app.schemas.student import (
    StudentProfileCreate,
    StudentProfileRead,
    StudentProfileUpdate,
    StudentSkillCreate,
    StudentSkillRead,
)


class StudentService:
    def __init__(
        self,
        student_repo: StudentRepositoryProtocol,
        skill_repo: SkillRepositoryProtocol,
        user_repo: UserRepositoryProtocol,
    ):
        self.student_repo = student_repo
        self.skill_repo = skill_repo
        self.user_repo = user_repo

    def _to_profile_read(self, profile: StudentProfile) -> StudentProfileRead:
        skills = self.student_repo.get_skills(profile.student_id)
        skill_reads = []
        for s in skills:
            skill_reads.append(
                StudentSkillRead(
                    id=s.id,
                    student_profile_id=s.student_id,
                    skill_id=s.skill_id,
                    skill_name=s.skill_name or f"Skill #{s.skill_id}",
                    category=s.category or "General",
                    proficiency=s.proficiency,
                    created_at=profile.created_at,
                    updated_at=profile.updated_at,
                )
            )

        return StudentProfileRead(
            id=profile.student_id,
            user_id=profile.user_id,
            full_name=profile.name,
            email=profile.email,
            headline=profile.headline,
            bio=None,
            education=None,
            graduation_year=None,
            skills=skill_reads,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def get_or_create_student_by_user(
        self, user_or_id: Any, requesting_user: Optional[User] = None
    ) -> StudentProfileRead:
        if isinstance(user_or_id, User):
            user = user_or_id
            user_id = user.id
        else:
            user_id = int(user_or_id)
            user = self.user_repo.get_by_id(user_id) if self.user_repo else None

        if requesting_user and requesting_user.role == Role.STUDENT and requesting_user.id != user_id:
            raise PermissionDeniedException("Access denied: You cannot view another student's profile")

        profile = self.student_repo.get_student_by_user_id(user_id)
        if not profile:
            profile = self.student_repo.create_student(
                StudentProfile(
                    student_id=0,
                    name=user.full_name if user else f"Student {user_id}",
                    email=user.email if user else f"student_{user_id}@example.com",
                    user_id=user_id,
                )
            )
        return self._to_profile_read(profile)

    def get_student(self, student_id: int, requesting_user: User) -> StudentProfileRead:
        profile = self.student_repo.get_student_by_id(student_id)
        if not profile:
            profile = self.student_repo.get_student_by_user_id(student_id)
        if not profile:
            raise ResourceNotFoundException(f"Student with ID {student_id} not found")

        # Privacy test: Student A cannot view Student B
        if requesting_user.role == Role.STUDENT and requesting_user.id != profile.user_id:
            raise PermissionDeniedException("Access denied: You cannot view another student's profile")

        return self._to_profile_read(profile)

    def update_student(
        self, student_id: int, req: StudentProfileUpdate, requesting_user: User
    ) -> StudentProfileRead:
        profile = self.student_repo.get_student_by_id(student_id)
        if not profile:
            profile = self.student_repo.get_student_by_user_id(student_id)
        if not profile:
            raise ResourceNotFoundException(f"Student with ID {student_id} not found")

        # Privacy test: Student A cannot update Student B
        if requesting_user.role == Role.STUDENT and requesting_user.id != profile.user_id:
            raise PermissionDeniedException("Access denied: You cannot modify another student's profile")

        if req.headline is not None:
            profile.headline = req.headline

        updated = self.student_repo.update_student(profile)
        emit_audit_event(
            action="STUDENT_PROFILE_UPDATED",
            actor_id=requesting_user.id,
            actor_role=requesting_user.role.value,
            target_type="student",
            target_id=str(updated.student_id),
        )
        return self._to_profile_read(updated)

    def list_students(
        self, requesting_user: User, skip: int = 0, limit: int = 50
    ) -> Tuple[List[StudentProfileRead], int]:
        if requesting_user.role != Role.ADMIN:
            raise PermissionDeniedException("Only administrators can list all students")

        profiles, total = self.student_repo.list_students(skip=skip, limit=limit)
        return [self._to_profile_read(p) for p in profiles], total

    def list_student_skills(self, student_id: int, requesting_user: User) -> List[StudentSkillRead]:
        profile = self.student_repo.get_student_by_id(student_id)
        if not profile:
            profile = self.student_repo.get_student_by_user_id(student_id)
        if not profile:
            raise ResourceNotFoundException(f"Student with ID {student_id} not found")

        if requesting_user.role == Role.STUDENT and requesting_user.id != profile.user_id:
            raise PermissionDeniedException("Access denied: You cannot view another student's skills")

        skills = self.student_repo.get_skills(profile.student_id)
        results = []
        for s in skills:
            results.append(
                StudentSkillRead(
                    id=s.id,
                    student_profile_id=profile.student_id,
                    skill_id=s.skill_id,
                    skill_name=s.skill_name or f"Skill #{s.skill_id}",
                    category=s.category or "General",
                    proficiency=s.proficiency,
                    created_at=profile.created_at,
                    updated_at=profile.updated_at,
                )
            )
        return results

    def upsert_student_skill(
        self, student_id: int, req: StudentSkillCreate, requesting_user: User
    ) -> StudentSkillRead:
        profile = self.student_repo.get_student_by_id(student_id)
        if not profile:
            profile = self.student_repo.get_student_by_user_id(student_id)
        if not profile:
            raise ResourceNotFoundException(f"Student with ID {student_id} not found")

        # Privacy test: Student A cannot manage Student B's skills
        if requesting_user.role == Role.STUDENT and requesting_user.id != profile.user_id:
            raise PermissionDeniedException("Access denied: You cannot modify another student's skills")

        catalog_skill = None
        if req.skill_id:
            catalog_skill = self.skill_repo.get_by_id(req.skill_id)
            if not catalog_skill:
                raise ResourceNotFoundException(f"Skill with ID {req.skill_id} not found in catalog")
        elif req.skill_name:
            norm = req.skill_name.strip().lower()
            catalog_skill = self.skill_repo.get_by_normalized_name(norm)
            if not catalog_skill:
                catalog_skill = self.skill_repo.create(
                    SkillCatalog(
                        id=None,
                        name=req.skill_name.strip(),
                        normalized_name=norm,
                        category=req.category or "General",
                        description=f"Registered competency: {req.skill_name.strip()}",
                    )
                )
        else:
            raise ValidationException("Either skill_id or skill_name must be provided")

        saved = self.student_repo.upsert_skill(profile.student_id, catalog_skill.id, req.proficiency)

        emit_audit_event(
            action="STUDENT_SKILL_UPSERTED",
            actor_id=requesting_user.id,
            actor_role=requesting_user.role.value,
            target_type="student_skill",
            target_id=str(saved.id),
            details={"skill_id": catalog_skill.id, "proficiency": req.proficiency},
        )

        return StudentSkillRead(
            id=saved.id,
            student_profile_id=profile.student_id,
            skill_id=saved.skill_id,
            skill_name=catalog_skill.name,
            category=catalog_skill.category,
            proficiency=saved.proficiency,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def delete_student_skill(
        self, student_id: int, skill_id: int, requesting_user: User
    ) -> bool:
        profile = self.student_repo.get_student_by_id(student_id)
        if not profile:
            profile = self.student_repo.get_student_by_user_id(student_id)
        if not profile:
            raise ResourceNotFoundException(f"Student with ID {student_id} not found")

        if requesting_user.role == Role.STUDENT and requesting_user.id != profile.user_id:
            raise PermissionDeniedException("Access denied: You cannot delete another student's skills")

        deleted = self.student_repo.delete_skill(profile.student_id, skill_id)
        if not deleted:
            raise ResourceNotFoundException(f"Skill ID {skill_id} not associated with this student")

        emit_audit_event(
            action="STUDENT_SKILL_DELETED",
            actor_id=requesting_user.id,
            actor_role=requesting_user.role.value,
            target_type="student_skill",
            target_id=str(skill_id),
            details={"student_id": profile.student_id},
        )
        return True

    # Compatibility methods
    get_profile_by_user_id = get_or_create_student_by_user
    get_profile_by_id = get_student
    update_profile = update_student
    list_profiles = list_students
