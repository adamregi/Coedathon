from typing import List, Optional, Tuple
from app.core.audit import emit_audit_event
from app.core.errors import (
    PermissionDeniedException,
    ResourceConflictException,
    ResourceNotFoundException,
)
from app.domain.models import Job, JobRequirement, Role, User
from app.domain.protocols import JobRepositoryProtocol, SkillRepositoryProtocol
from app.schemas.job import (
    JobCreate,
    JobRead,
    JobRequirementRead,
    JobRequirementUpsert,
    JobUpdate,
)


class JobService:
    def __init__(self, job_repo: JobRepositoryProtocol, skill_repo: SkillRepositoryProtocol):
        self.job_repo = job_repo
        self.skill_repo = skill_repo

    def _enrich_requirements(self, requirements: List[JobRequirement]) -> List[JobRequirementRead]:
        enriched = []
        for req in requirements:
            skill = self.skill_repo.get_by_id(req.skill_id)
            enriched.append(
                JobRequirementRead(
                    id=req.id,
                    job_id=req.job_id,
                    skill_id=req.skill_id,
                    skill_name=skill.name if skill else None,
                    category=skill.category if skill else None,
                    required_proficiency=req.required_proficiency,
                    mandatory=req.mandatory,
                    created_at=req.created_at,
                )
            )
        return enriched

    def _to_job_read(self, job: Job) -> JobRead:
        return JobRead(
            id=job.id,
            employer_id=job.employer_id,
            title=job.title,
            company_name=job.company_name,
            description=job.description,
            department=job.department,
            location=job.location,
            salary_range=job.salary_range,
            is_active=job.is_active,
            requirements=self._enrich_requirements(job.requirements),
            created_at=job.created_at,
            updated_at=getattr(job, "updated_at", job.created_at),
        )

    def create_job(self, req: JobCreate, employer: User) -> JobRead:
        if employer.role not in (Role.EMPLOYER, Role.ADMIN):
            raise PermissionDeniedException("Only employers or admins can post jobs")

        # Validate unique skills in initial requirements
        skill_ids = [r.skill_id for r in req.requirements]
        if len(skill_ids) != len(set(skill_ids)):
            raise ResourceConflictException("Duplicate skill requirement in job creation")

        # Validate each skill exists
        req_entities = []
        for r in req.requirements:
            skill = self.skill_repo.get_by_id(r.skill_id)
            if not skill:
                raise ResourceNotFoundException(f"Skill ID {r.skill_id} not found in catalog")
            req_entities.append(
                JobRequirement(
                    id=0,
                    job_id=0,
                    skill_id=r.skill_id,
                    required_proficiency=r.required_proficiency,
                    mandatory=r.mandatory,
                )
            )

        job = Job(
            id=0,
            employer_id=employer.id,
            title=req.title,
            company_name=req.company_name,
            description=req.description,
            department=req.department,
            location=req.location,
            salary_range=req.salary_range,
            is_active=req.is_active,
            requirements=req_entities,
        )
        created = self.job_repo.create_job(job)

        emit_audit_event(
            action="JOB_CREATED",
            actor_id=employer.id,
            actor_role=employer.role.value,
            target_type="job",
            target_id=str(created.id),
            details={"title": created.title, "company": created.company_name},
        )

        return self._to_job_read(created)

    def get_job(self, job_id: int) -> JobRead:
        job = self.job_repo.get_job_by_id(job_id)
        if not job:
            raise ResourceNotFoundException(f"Job with ID {job_id} not found")
        return self._to_job_read(job)

    def update_job(self, job_id: int, req: JobUpdate, actor: User) -> JobRead:
        job = self.job_repo.get_job_by_id(job_id)
        if not job:
            raise ResourceNotFoundException(f"Job with ID {job_id} not found")

        # Ownership check
        if actor.role == Role.EMPLOYER and job.employer_id != actor.id:
            raise PermissionDeniedException("Employers can only update their own job postings")

        if req.title is not None:
            job.title = req.title
        if req.company_name is not None:
            job.company_name = req.company_name
        if req.description is not None:
            job.description = req.description
        if req.department is not None:
            job.department = req.department
        if req.location is not None:
            job.location = req.location
        if req.salary_range is not None:
            job.salary_range = req.salary_range
        if req.is_active is not None:
            job.is_active = req.is_active

        updated = self.job_repo.update_job(job)

        emit_audit_event(
            action="JOB_UPDATED",
            actor_id=actor.id,
            actor_role=actor.role.value,
            target_type="job",
            target_id=str(updated.id),
        )

        return self._to_job_read(updated)

    def delete_job(self, job_id: int, actor: User) -> bool:
        job = self.job_repo.get_job_by_id(job_id)
        if not job:
            raise ResourceNotFoundException(f"Job with ID {job_id} not found")

        if actor.role == Role.EMPLOYER and job.employer_id != actor.id:
            raise PermissionDeniedException("Employers can only delete their own job postings")

        success = self.job_repo.delete_job(job_id)

        emit_audit_event(
            action="JOB_DELETED",
            actor_id=actor.id,
            actor_role=actor.role.value,
            target_type="job",
            target_id=str(job_id),
            details={"title": job.title},
        )

        return success

    def list_jobs(
        self,
        employer_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[JobRead], int]:
        jobs, total = self.job_repo.list_jobs(
            employer_id=employer_id,
            is_active=is_active,
            search=search,
            skip=skip,
            limit=limit,
        )
        return [self._to_job_read(j) for j in jobs], total

    def upsert_requirement(
        self, job_id: int, req: JobRequirementUpsert, actor: User
    ) -> JobRequirementRead:
        job = self.job_repo.get_job_by_id(job_id)
        if not job:
            raise ResourceNotFoundException(f"Job with ID {job_id} not found")

        if actor.role == Role.EMPLOYER and job.employer_id != actor.id:
            raise PermissionDeniedException("Employers can only modify requirements for their own jobs")

        skill = self.skill_repo.get_by_id(req.skill_id)
        if not skill:
            raise ResourceNotFoundException(f"Skill ID {req.skill_id} not found in catalog")

        entity = JobRequirement(
            id=0,
            job_id=job_id,
            skill_id=req.skill_id,
            required_proficiency=req.required_proficiency,
            mandatory=req.mandatory,
        )
        saved = self.job_repo.upsert_requirement(entity)

        emit_audit_event(
            action="JOB_REQUIREMENT_UPSERTED",
            actor_id=actor.id,
            actor_role=actor.role.value,
            target_type="job_requirement",
            target_id=str(saved.id),
            details={"job_id": job_id, "skill_id": req.skill_id, "mandatory": req.mandatory},
        )

        return JobRequirementRead(
            id=saved.id,
            job_id=saved.job_id,
            skill_id=saved.skill_id,
            skill_name=skill.name,
            category=skill.category,
            required_proficiency=saved.required_proficiency,
            mandatory=saved.mandatory,
            created_at=saved.created_at,
        )

    def delete_requirement(self, job_id: int, skill_id: int, actor: User) -> bool:
        job = self.job_repo.get_job_by_id(job_id)
        if not job:
            raise ResourceNotFoundException(f"Job with ID {job_id} not found")

        if actor.role == Role.EMPLOYER and job.employer_id != actor.id:
            raise PermissionDeniedException("Employers can only modify requirements for their own jobs")

        success = self.job_repo.delete_requirement(job_id, skill_id)
        if not success:
            raise ResourceNotFoundException(f"Requirement with skill ID {skill_id} not found on job {job_id}")
        return True

    def get_job_skills(self, job_id: int) -> List[JobRequirementRead]:
        job = self.job_repo.get_job_by_id(job_id)
        if not job:
            raise ResourceNotFoundException(f"Job with ID {job_id} not found")
        return self._enrich_requirements(job.skills)

    upsert_job_skill = upsert_requirement
    delete_job_skill = delete_requirement
