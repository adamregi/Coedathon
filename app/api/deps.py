from typing import Callable, List, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.errors import AuthenticationException, PermissionDeniedException
from app.core.security import decode_token
from app.domain.models import Role, User
from app.repositories.in_memory import RepositoryContainer, default_repositories
from app.services.application_service import ApplicationService
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService
from app.services.job_service import JobService
from app.services.matching_service import MatchingService
from app.services.skill_service import SkillService
from app.services.student_service import StudentService

bearer_scheme = HTTPBearer(auto_error=False)


def get_repo_container(db: Session = Depends(get_db)) -> RepositoryContainer:
    return RepositoryContainer(db=db)


def get_auth_service(
    repos: RepositoryContainer = Depends(get_repo_container),
) -> AuthService:
    return AuthService(repos.user_repo, repos.student_repo)


def get_skill_service(
    repos: RepositoryContainer = Depends(get_repo_container),
) -> SkillService:
    return SkillService(repos.skill_repo)


def get_student_service(
    repos: RepositoryContainer = Depends(get_repo_container),
) -> StudentService:
    return StudentService(repos.student_repo, repos.skill_repo, repos.user_repo)


def get_job_service(
    repos: RepositoryContainer = Depends(get_repo_container),
) -> JobService:
    return JobService(repos.job_repo, repos.skill_repo)


def get_matching_service(
    repos: RepositoryContainer = Depends(get_repo_container),
) -> MatchingService:
    return MatchingService(
        repos.matching_repo,
        repos.job_repo,
        repos.student_repo,
        repos.skill_repo,
        repos.user_repo,
    )


def get_application_service(
    repos: RepositoryContainer = Depends(get_repo_container),
    matching_svc: MatchingService = Depends(get_matching_service),
) -> ApplicationService:
    return ApplicationService(
        repos.application_repo,
        repos.job_repo,
        matching_svc,
        repos.user_repo,
    )


def get_dashboard_service(
    repos: RepositoryContainer = Depends(get_repo_container),
) -> DashboardService:
    return DashboardService(
        repos.user_repo,
        repos.skill_repo,
        repos.student_repo,
        repos.job_repo,
        repos.matching_repo,
        repos.application_repo,
    )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    repos: RepositoryContainer = Depends(get_repo_container),
) -> User:
    if not credentials:
        raise AuthenticationException("Bearer token missing from Authorization header")

    token = credentials.credentials
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise AuthenticationException("Provided token is not an access token")

    user_id = int(payload.get("sub", 0))
    user = repos.user_repo.get_by_id(user_id)
    if not user:
        raise AuthenticationException("User not found")
    if not user.is_active:
        raise AuthenticationException("User account is disabled")

    return user


def require_role(*allowed_roles: Role) -> Callable[[User], User]:
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise PermissionDeniedException(
                f"Role '{current_user.role.value}' is not authorized. Required: {[r.value for r in allowed_roles]}"
            )
        return current_user

    return role_checker


require_admin = require_role(Role.ADMIN)
require_student = require_role(Role.STUDENT)
require_employer = require_role(Role.EMPLOYER)
require_employer_or_admin = require_role(Role.EMPLOYER, Role.ADMIN)
