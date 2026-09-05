import pytest
from starlette.testclient import TestClient

from app.api.deps import get_repo_container
from app.core.security import create_access_token, hash_password
from app.domain.models import Role, User
from app.main import app
from app.repositories.in_memory import RepositoryContainer


@pytest.fixture
def repo_container() -> RepositoryContainer:
    """Provides a clean, isolated in-memory repository container for testing."""
    return RepositoryContainer()


@pytest.fixture
def client(repo_container: RepositoryContainer):
    """Provides a TestClient with dependency overrides to isolate state per test."""
    app.dependency_overrides[get_repo_container] = lambda: repo_container
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(repo_container: RepositoryContainer) -> User:
    admin = User(
        id=0,
        email="admin@platform.com",
        hashed_password=hash_password("AdminSecurePassword123!"),
        full_name="Platform Administrator",
        role=Role.ADMIN,
    )
    return repo_container.user_repo.create(admin)


@pytest.fixture
def student_user(repo_container: RepositoryContainer) -> User:
    from app.domain.models import StudentProfile
    student = User(
        id=0,
        email="student@university.edu",
        hashed_password=hash_password("StudentSecurePassword123!"),
        full_name="Alice Student",
        role=Role.STUDENT,
    )
    u = repo_container.user_repo.create(student)
    repo_container.student_repo.create_student(
        StudentProfile(
            student_id=0,
            name=u.full_name,
            email=u.email,
            user_id=u.id,
        )
    )
    return u


@pytest.fixture
def employer_user(repo_container: RepositoryContainer) -> User:
    employer = User(
        id=0,
        email="recruiter@techcorp.com",
        hashed_password=hash_password("EmployerSecurePassword123!"),
        full_name="Bob Recruiter",
        role=Role.EMPLOYER,
    )
    return repo_container.user_repo.create(employer)


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token(user_id=admin_user.id, role=admin_user.role.value)


@pytest.fixture
def student_token(student_user: User) -> str:
    return create_access_token(user_id=student_user.id, role=student_user.role.value)


@pytest.fixture
def employer_token(employer_user: User) -> str:
    return create_access_token(user_id=employer_user.id, role=employer_user.role.value)


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def student_headers(student_token: str) -> dict:
    return {"Authorization": f"Bearer {student_token}"}


@pytest.fixture
def employer_headers(employer_token: str) -> dict:
    return {"Authorization": f"Bearer {employer_token}"}
