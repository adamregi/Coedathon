from typing import List, Optional, Tuple
from app.core.audit import emit_audit_event
from app.core.errors import (
    InvalidStateTransitionException,
    PermissionDeniedException,
    ResourceConflictException,
    ResourceNotFoundException,
)
from app.domain.models import Application, ApplicationStatus, Role, User
from app.domain.protocols import (
    ApplicationRepositoryProtocol,
    JobRepositoryProtocol,
    UserRepositoryProtocol,
)
from app.schemas.application import ApplicationRead
from app.services.matching_service import MatchingService


class ApplicationService:
    # State transition mapping: Current Status -> Set of Allowed Next Statuses (for employer)
    EMPLOYER_VALID_TRANSITIONS = {
        ApplicationStatus.SUBMITTED: {ApplicationStatus.REVIEWED},
        ApplicationStatus.REVIEWED: {ApplicationStatus.SHORTLISTED, ApplicationStatus.REJECTED},
        ApplicationStatus.SHORTLISTED: {ApplicationStatus.CLOSED},
        ApplicationStatus.REJECTED: {ApplicationStatus.CLOSED},
        ApplicationStatus.CLOSED: set(),
        ApplicationStatus.WITHDRAWN: set(),
    }

    STUDENT_ALLOWED_WITHDRAW_FROM = {
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.REVIEWED,
        ApplicationStatus.SHORTLISTED,
    }

    def __init__(
        self,
        application_repo: ApplicationRepositoryProtocol,
        job_repo: JobRepositoryProtocol,
        matching_service: MatchingService,
        user_repo: UserRepositoryProtocol,
    ):
        self.application_repo = application_repo
        self.job_repo = job_repo
        self.matching_service = matching_service
        self.user_repo = user_repo

    def submit_application(self, student_id: int, job_id: int, student_user: User) -> ApplicationRead:
        if student_user.role == Role.STUDENT and student_user.id != student_id:
            raise PermissionDeniedException("Students can only apply on their own behalf")

        job = self.job_repo.get_job_by_id(job_id)
        if not job or not job.is_active:
            raise ResourceNotFoundException(f"Active job with ID {job_id} not found")

        # Check for existing active application
        existing = self.application_repo.get_active_application(student_id, job_id)
        if existing:
            raise ResourceConflictException(
                f"An active application already exists for this job with status '{existing.status.value}'"
            )

        # Compute match percentage snapshot
        analysis = self.matching_service.calculate_and_save_analysis(student_id, job_id, student_user)
        snapshot_score = analysis.overall_match_percentage

        application = Application(
            id=0,
            student_id=student_id,
            job_id=job_id,
            status=ApplicationStatus.SUBMITTED,
            match_percentage_snapshot=snapshot_score,
        )
        created = self.application_repo.create_application(application)

        emit_audit_event(
            action="APPLICATION_SUBMITTED",
            actor_id=student_user.id,
            actor_role=student_user.role.value,
            target_type="application",
            target_id=str(created.id),
            details={
                "job_id": job_id,
                "match_percentage_snapshot": snapshot_score,
            },
        )

        return self._to_read(created, job=job, student=student_user)

    def withdraw_application(self, application_id: int, student_user: User) -> ApplicationRead:
        app = self.application_repo.get_application_by_id(application_id)
        if not app:
            raise ResourceNotFoundException(f"Application with ID {application_id} not found")

        if student_user.role == Role.STUDENT and app.student_id != student_user.id:
            raise PermissionDeniedException("You can only withdraw your own applications")

        if app.status not in self.STUDENT_ALLOWED_WITHDRAW_FROM:
            raise InvalidStateTransitionException(
                f"Cannot withdraw application in status '{app.status.value}'"
            )

        old_status = app.status
        app.status = ApplicationStatus.WITHDRAWN
        updated = self.application_repo.update_application(app)

        emit_audit_event(
            action="APPLICATION_WITHDRAWN",
            actor_id=student_user.id,
            actor_role=student_user.role.value,
            target_type="application",
            target_id=str(updated.id),
            details={"previous_status": old_status.value},
        )

        return self._to_read(updated)

    def transition_status(
        self, application_id: int, new_status: ApplicationStatus, actor: User
    ) -> ApplicationRead:
        app = self.application_repo.get_application_by_id(application_id)
        if not app:
            raise ResourceNotFoundException(f"Application with ID {application_id} not found")

        job = self.job_repo.get_job_by_id(app.job_id)
        if not job:
            raise ResourceNotFoundException(f"Associated job {app.job_id} not found")

        # Ownership check: only the employer owning the job (or admin) can transition
        if actor.role == Role.EMPLOYER and job.employer_id != actor.id:
            raise PermissionDeniedException("Employers can only update application statuses for their own jobs")

        allowed_next = self.EMPLOYER_VALID_TRANSITIONS.get(app.status, set())
        if new_status not in allowed_next and actor.role != Role.ADMIN:
            raise InvalidStateTransitionException(
                f"Invalid transition from '{app.status.value}' to '{new_status.value}'. Allowed transitions: {[s.value for s in allowed_next]}"
            )

        old_status = app.status
        app.status = new_status
        updated = self.application_repo.update_application(app)

        emit_audit_event(
            action="APPLICATION_STATUS_TRANSITIONED",
            actor_id=actor.id,
            actor_role=actor.role.value,
            target_type="application",
            target_id=str(updated.id),
            details={"from_status": old_status.value, "to_status": new_status.value},
        )

        return self._to_read(updated, job=job)

    def get_application(self, application_id: int, actor: User) -> ApplicationRead:
        app = self.application_repo.get_application_by_id(application_id)
        if not app:
            raise ResourceNotFoundException(f"Application with ID {application_id} not found")

        job = self.job_repo.get_job_by_id(app.job_id)

        # Check access: student must own it, or employer must own the job, or admin
        if actor.role == Role.STUDENT and app.student_id != actor.id:
            raise PermissionDeniedException("Students can only view their own applications")
        if actor.role == Role.EMPLOYER and job and job.employer_id != actor.id:
            raise PermissionDeniedException("Employers can only view applications for their own jobs")

        return self._to_read(app, job=job)

    def list_applications(
        self,
        actor: User,
        student_id: Optional[int] = None,
        job_id: Optional[int] = None,
        status: Optional[ApplicationStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[ApplicationRead], int]:
        if actor.role == Role.STUDENT:
            student_id = actor.id
        elif actor.role == Role.EMPLOYER:
            if job_id:
                job = self.job_repo.get_job_by_id(job_id)
                if not job or job.employer_id != actor.id:
                    raise PermissionDeniedException("You do not own this job")
            else:
                # Employer listing all their job applications
                # We filter by employer's jobs
                employer_jobs, _ = self.job_repo.list_jobs(employer_id=actor.id, limit=1000)
                job_ids = {j.id for j in employer_jobs}
                all_apps, total = self.application_repo.list_applications(
                    student_id=student_id, status=status, skip=0, limit=10000
                )
                filtered = [a for a in all_apps if a.job_id in job_ids]
                return [self._to_read(a) for a in filtered[skip : skip + limit]], len(filtered)

        apps, total = self.application_repo.list_applications(
            student_id=student_id, job_id=job_id, status=status, skip=skip, limit=limit
        )
        return [self._to_read(a) for a in apps], total

    def _to_read(
        self,
        app: Application,
        job: Optional[Job] = None,
        student: Optional[User] = None,
    ) -> ApplicationRead:
        if not job:
            job = self.job_repo.get_job_by_id(app.job_id)
        if not student:
            student = self.user_repo.get_by_id(app.student_id)

        return ApplicationRead(
            id=app.id,
            student_id=app.student_id,
            student_name=student.full_name if student else None,
            job_id=app.job_id,
            job_title=job.title if job else None,
            company_name=job.company_name if job else None,
            status=app.status,
            match_percentage_snapshot=app.match_percentage_snapshot,
            created_at=app.created_at,
            updated_at=app.updated_at,
        )
