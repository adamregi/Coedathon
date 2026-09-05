import pytest
from app.domain.models import Job, JobRequirement, Role, SkillCatalog, StudentProfile, StudentSkill, User
from app.repositories.in_memory import RepositoryContainer
from app.services.matching_service import MatchingService


def test_matching_engine_gap_and_weighted_average():
    repos = RepositoryContainer()
    service = MatchingService(
        repos.matching_repo,
        repos.job_repo,
        repos.student_repo,
        repos.skill_repo,
        repos.user_repo,
    )

    # 1. Setup skills
    py_skill = repos.skill_repo.create(
        SkillCatalog(id=0, name="Python", normalized_name="python", category="Backend")
    )
    sql_skill = repos.skill_repo.create(
        SkillCatalog(id=0, name="SQL", normalized_name="sql", category="Database")
    )
    docker_skill = repos.skill_repo.create(
        SkillCatalog(id=0, name="Docker", normalized_name="docker", category="DevOps")
    )

    # 2. Setup student: Python level 4, SQL missing (level 0), Docker level 2
    student = repos.user_repo.create(
        User(id=0, email="s@test.com", hashed_password="pw", full_name="Student", role=Role.STUDENT)
    )
    profile = repos.student_repo.create_profile(StudentProfile(id=0, user_id=student.id))
    repos.student_repo.upsert_skill(profile.id, StudentSkill(id=0, student_profile_id=profile.id, skill_id=py_skill.id, proficiency=4))
    repos.student_repo.upsert_skill(profile.id, StudentSkill(id=0, student_profile_id=profile.id, skill_id=docker_skill.id, proficiency=2))

    # 3. Setup job requirements:
    # - Python: required 5, mandatory=True (weight 2) -> ratio = 4/5 = 0.80 -> weighted = 2 * 80 = 160
    # - SQL: required 3, mandatory=True (weight 2) -> missing (level 0) -> ratio = 0/3 = 0.0 -> weighted = 2 * 0 = 0
    # - Docker: required 2, mandatory=False (weight 1) -> ratio = 2/2 = 1.00 -> weighted = 1 * 100 = 100
    # Total weight: 2 + 2 + 1 = 5
    # Weighted sum: 160 + 0 + 100 = 260
    # Weighted average: 260 / 5 = 52.0% -> round = 52
    job = repos.job_repo.create_job(
        Job(
            id=0,
            employer_id=99,
            title="Backend Engineer",
            company_name="Tech Co",
            description="Desc",
            requirements=[
                JobRequirement(id=0, job_id=0, skill_id=py_skill.id, required_proficiency=5, mandatory=True),
                JobRequirement(id=0, job_id=0, skill_id=sql_skill.id, required_proficiency=3, mandatory=True),
                JobRequirement(id=0, job_id=0, skill_id=docker_skill.id, required_proficiency=2, mandatory=False),
            ],
        )
    )

    result = service.calculate_and_save_analysis(student.id, job.id, actor=student)

    assert result.overall_match_percentage == 52
    assert len(result.skill_results) == 3

    # Check gap calculations
    results_map = {r.skill_id: r for r in result.skill_results}
    assert results_map[py_skill.id].gap == 1
    assert results_map[py_skill.id].matched is False
    assert results_map[sql_skill.id].gap == 3
    assert results_map[sql_skill.id].current_proficiency == 0  # missing skill defaults to 0
    assert results_map[sql_skill.id].matched is False
    assert results_map[docker_skill.id].gap == 0
    assert results_map[docker_skill.id].matched is True


def test_recommendation_prioritization():
    """
    Persist one recommendation per unmet requirement.
    Prioritize mandatory gaps before optional gaps, then larger gaps.
    """
    repos = RepositoryContainer()
    service = MatchingService(
        repos.matching_repo,
        repos.job_repo,
        repos.student_repo,
        repos.skill_repo,
        repos.user_repo,
    )

    s1 = repos.skill_repo.create(SkillCatalog(id=0, name="S1", normalized_name="s1", category="Cat"))
    s2 = repos.skill_repo.create(SkillCatalog(id=0, name="S2", normalized_name="s2", category="Cat"))
    s3 = repos.skill_repo.create(SkillCatalog(id=0, name="S3", normalized_name="s3", category="Cat"))

    student = repos.user_repo.create(
        User(id=0, email="s2@test.com", hashed_password="pw", full_name="Student", role=Role.STUDENT)
    )
    profile = repos.student_repo.create_profile(StudentProfile(id=0, user_id=student.id))
    # S1: level 2; S2: level 0; S3: level 1
    repos.student_repo.upsert_skill(profile.id, StudentSkill(id=0, student_profile_id=profile.id, skill_id=s1.id, proficiency=2))
    repos.student_repo.upsert_skill(profile.id, StudentSkill(id=0, student_profile_id=profile.id, skill_id=s3.id, proficiency=1))

    # Requirements:
    # S1: required 3, mandatory=False -> gap = 1 (optional)
    # S2: required 3, mandatory=True -> gap = 3 (mandatory)
    # S3: required 4, mandatory=True -> gap = 3 (mandatory)
    job = repos.job_repo.create_job(
        Job(
            id=0,
            employer_id=99,
            title="Dev",
            company_name="Co",
            description="Desc",
            requirements=[
                JobRequirement(id=0, job_id=0, skill_id=s1.id, required_proficiency=3, mandatory=False),
                JobRequirement(id=0, job_id=0, skill_id=s2.id, required_proficiency=3, mandatory=True),
                JobRequirement(id=0, job_id=0, skill_id=s3.id, required_proficiency=4, mandatory=True),
            ],
        )
    )

    result = service.calculate_and_save_analysis(student.id, job.id, actor=student)
    recs = result.recommendations

    assert len(recs) == 3
    # First 2 must be mandatory (S2, S3)
    assert recs[0].priority == "high"
    assert recs[1].priority == "high"
    # Optional gap of 1 is last with low priority
    assert recs[2].skill_id == s1.id
    assert recs[2].priority == "low"


def test_matching_with_no_requirements():
    repos = RepositoryContainer()
    service = MatchingService(
        repos.matching_repo,
        repos.job_repo,
        repos.student_repo,
        repos.skill_repo,
        repos.user_repo,
    )
    student = repos.user_repo.create(
        User(id=0, email="s3@test.com", hashed_password="pw", full_name="Student", role=Role.STUDENT)
    )
    job = repos.job_repo.create_job(
        Job(
            id=0,
            employer_id=99,
            title="General Hand",
            company_name="Co",
            description="No skills required",
            requirements=[],
        )
    )

    result = service.calculate_and_save_analysis(student.id, job.id, actor=student)
    assert result.overall_match_percentage == 100
    assert len(result.recommendations) == 0
