import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import (
    AnalysisItemORM,
    AnalysisRunORM,
    ApplicationORM,
    JobORM,
    JobSkillORM,
    RecommendationORM,
    SkillORM,
    StudentORM,
    StudentSkillORM,
    UserORM,
)
from app.domain.models import ApplicationStatus
from app.repositories.mysql_repo import (
    MySQLApplicationRepository,
    MySQLJobRepository,
    MySQLMatchingRepository,
    MySQLSkillRepository,
    MySQLStudentRepository,
    MySQLUserRepository,
)
from app.domain.models import (
    AnalysisItem,
    AnalysisRun,
    Application,
    Job,
    JobSkill,
    Recommendation,
    SkillCatalog,
    StudentProfile,
    StudentSkill,
    User,
    Role,
)


@pytest.fixture
def db_session():
    """Create an isolated database engine and session for integration testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_table_creation_and_canonical_models(db_session):
    # Verify all 10 tables exist
    tables = Base.metadata.tables.keys()
    assert "users" in tables
    assert "students" in tables
    assert "skills" in tables
    assert "student_skills" in tables
    assert "jobs" in tables
    assert "job_skills" in tables
    assert "analysis_runs" in tables
    assert "analysis_items" in tables
    assert "recommendations" in tables
    assert "applications" in tables


def test_mysql_repositories_crud_and_relationships(db_session):
    user_repo = MySQLUserRepository(db_session)
    student_repo = MySQLStudentRepository(db_session)
    skill_repo = MySQLSkillRepository(db_session)
    job_repo = MySQLJobRepository(db_session)
    matching_repo = MySQLMatchingRepository(db_session)
    app_repo = MySQLApplicationRepository(db_session)

    # 1. Create User & Student
    user = user_repo.create(
        User(id=0, email="mysql_test@test.com", hashed_password="pw", full_name="MySQL Tester", role=Role.STUDENT)
    )
    assert user.id > 0

    student = student_repo.create_student(
        StudentProfile(student_id=0, name="MySQL Tester", email="mysql_test@test.com", user_id=user.id, headline="Engineer")
    )
    assert student.student_id > 0

    # 2. Create Skills
    s1 = skill_repo.create(SkillCatalog(id=0, name="Python", normalized_name="python", category="Backend"))
    s2 = skill_repo.create(SkillCatalog(id=0, name="MySQL", normalized_name="mysql", category="Database"))

    # 3. Add student skill
    student_repo.upsert_skill(student.student_id, s1.id, 4)
    skills = student_repo.get_skills(student.student_id)
    assert len(skills) == 1
    assert skills[0].proficiency == 4

    # 4. Create Job & Job Skills
    job = job_repo.create_job(
        Job(
            id=0,
            employer_id=user.id,
            title="Backend Lead",
            company_name="MySQL Corp",
            description="Leading backend development",
            skills=[
                JobSkill(id=0, job_id=0, skill_id=s1.id, required_level=4, mandatory=True),
                JobSkill(id=0, job_id=0, skill_id=s2.id, required_level=3, mandatory=True),
            ],
        )
    )
    assert job.id > 0
    assert len(job.skills) == 2

    # 5. Persist Analysis Run, Items, and Recommendations
    run = AnalysisRun(
        id="test-run-uuid-123",
        student_id=student.student_id,
        job_id=job.id,
        algorithm_version="v1.0",
        overall_match_percentage=50,
    )
    items = [
        AnalysisItem(id=0, analysis_run_id=run.id, skill_id=s1.id, required_level=4, current_level=4, gap=0, matched=True, mandatory=True),
        AnalysisItem(id=0, analysis_run_id=run.id, skill_id=s2.id, required_level=3, current_level=0, gap=3, matched=False, mandatory=True),
    ]
    recs = [
        Recommendation(
            id=0,
            student_id=student.student_id,
            job_id=job.id,
            skill_id=s2.id,
            current_level=0,
            target_level=3,
            analysis_run_id=run.id,
            priority="HIGH",
            reason="Mandatory job requirement",
        )
    ]
    saved_run = matching_repo.save_analysis(run, items, recs)
    assert saved_run.id == "test-run-uuid-123"

    # Fetch analysis run and verify independent items and recommendations
    fetched_run = matching_repo.get_analysis_run("test-run-uuid-123")
    assert fetched_run is not None
    assert len(fetched_run.items) == 2
    assert len(fetched_run.recommendations) == 1
    assert fetched_run.recommendations[0].reason == "Mandatory job requirement"

    # 6. Create Application with match percentage snapshot
    app = app_repo.create_application(
        Application(
            id=0,
            student_id=student.student_id,
            job_id=job.id,
            status=ApplicationStatus.SUBMITTED,
            match_percentage_snapshot=50,
        )
    )
    assert app.id > 0
    assert app.match_percentage_snapshot == 50

    # Verify duplicate active application is detected
    active_app = app_repo.get_active_application(student.student_id, job.id)
    assert active_app is not None
    assert active_app.id == app.id
