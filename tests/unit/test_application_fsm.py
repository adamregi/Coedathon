import pytest

from app.core.errors import (
    InvalidStateTransitionException,
    PermissionDeniedException,
    ResourceConflictException,
)
from app.domain.models import ApplicationStatus, Job, Role, User
from app.repositories.in_memory import RepositoryContainer
from app.services.application_service import ApplicationService
from app.services.matching_service import MatchingService


def setup_fsm_environment():
    repos = RepositoryContainer()
    matching_svc = MatchingService(
        repos.matching_repo,
        repos.job_repo,
        repos.student_repo,
        repos.skill_repo,
        repos.user_repo,
    )
    app_svc = ApplicationService(
        repos.application_repo,
        repos.job_repo,
        matching_svc,
        repos.user_repo,
    )

    employer = repos.user_repo.create(
        User(id=0, email="emp@test.com", hashed_password="pw", full_name="Employer", role=Role.EMPLOYER)
    )
    other_employer = repos.user_repo.create(
        User(id=0, email="emp2@test.com", hashed_password="pw", full_name="Other Employer", role=Role.EMPLOYER)
    )
    student = repos.user_repo.create(
        User(id=0, email="stu@test.com", hashed_password="pw", full_name="Student", role=Role.STUDENT)
    )
    job = repos.job_repo.create_job(
        Job(
            id=0,
            employer_id=employer.id,
            title="Software Developer",
            company_name="Acme Corp",
            description="Software dev position",
            requirements=[],
        )
    )

    return repos, app_svc, employer, other_employer, student, job


def test_application_lifecycle_happy_path():
    _, app_svc, employer, _, student, job = setup_fsm_environment()

    # 1. Student submits application
    app_record = app_svc.submit_application(student.id, job.id, student_user=student)
    assert app_record.status == ApplicationStatus.SUBMITTED
    assert app_record.match_percentage_snapshot == 100

    # 2. Employer reviews application
    app_record = app_svc.transition_status(app_record.id, ApplicationStatus.REVIEWED, actor=employer)
    assert app_record.status == ApplicationStatus.REVIEWED

    # 3. Employer shortlists application
    app_record = app_svc.transition_status(app_record.id, ApplicationStatus.SHORTLISTED, actor=employer)
    assert app_record.status == ApplicationStatus.SHORTLISTED

    # 4. Employer closes application
    app_record = app_svc.transition_status(app_record.id, ApplicationStatus.CLOSED, actor=employer)
    assert app_record.status == ApplicationStatus.CLOSED


def test_invalid_state_transition_rejected():
    _, app_svc, employer, _, student, job = setup_fsm_environment()

    app_record = app_svc.submit_application(student.id, job.id, student_user=student)

    # SUBMITTED cannot transition directly to SHORTLISTED or CLOSED
    with pytest.raises(InvalidStateTransitionException):
        app_svc.transition_status(app_record.id, ApplicationStatus.SHORTLISTED, actor=employer)

    with pytest.raises(InvalidStateTransitionException):
        app_svc.transition_status(app_record.id, ApplicationStatus.CLOSED, actor=employer)


def test_duplicate_active_application_prevented():
    _, app_svc, _, _, student, job = setup_fsm_environment()

    # First submission succeeds
    app_svc.submit_application(student.id, job.id, student_user=student)

    # Second active submission for same student/job fails
    with pytest.raises(ResourceConflictException):
        app_svc.submit_application(student.id, job.id, student_user=student)


def test_student_withdrawal_workflow():
    _, app_svc, _, _, student, job = setup_fsm_environment()

    app_record = app_svc.submit_application(student.id, job.id, student_user=student)
    withdrawn = app_svc.withdraw_application(app_record.id, student_user=student)
    assert withdrawn.status == ApplicationStatus.WITHDRAWN

    # Cannot withdraw again or transition withdrawn
    with pytest.raises(InvalidStateTransitionException):
        app_svc.withdraw_application(app_record.id, student_user=student)


def test_employer_ownership_enforcement():
    _, app_svc, _, other_employer, student, job = setup_fsm_environment()

    app_record = app_svc.submit_application(student.id, job.id, student_user=student)

    # Other employer cannot transition application status
    with pytest.raises(PermissionDeniedException):
        app_svc.transition_status(app_record.id, ApplicationStatus.REVIEWED, actor=other_employer)
