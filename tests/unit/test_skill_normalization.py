import pytest
from pydantic import ValidationError

from app.core.errors import ResourceConflictException
from app.domain.models import Role, User
from app.repositories.in_memory import RepositoryContainer
from app.schemas.skill import SkillCatalogCreate, normalize_skill_name
from app.services.skill_service import SkillService


def test_normalize_skill_name_helper():
    assert normalize_skill_name("  Python   FastAPI   ") == "Python FastAPI"
    assert normalize_skill_name("\tMachine   Learning \n") == "Machine Learning"
    assert normalize_skill_name("Rust") == "Rust"


def test_skill_catalog_schema_validation():
    # Whitespace collapse inside schema
    schema = SkillCatalogCreate(name="  Data    Science  ", category="  Analytics  ")
    assert schema.name == "Data Science"
    assert schema.category == "Analytics"

    # Empty after trim should fail validation
    with pytest.raises(ValidationError):
        SkillCatalogCreate(name="   ", category="General")


def test_skill_duplicate_prevention_case_insensitive():
    repos = RepositoryContainer()
    service = SkillService(repos.skill_repo)
    admin = User(id=1, email="a@a.com", hashed_password="pw", full_name="Admin", role=Role.ADMIN)

    # First insert
    service.create_skill(
        SkillCatalogCreate(name="Kubernetes Orchestration", category="DevOps"),
        actor_id=admin.id,
    )

    # Attempt to insert same name with different casing / spacing
    with pytest.raises(ResourceConflictException):
        service.create_skill(
            SkillCatalogCreate(name="  kubernetes   orchestration  ", category="Infrastructure"),
            actor_id=admin.id,
        )
