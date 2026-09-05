import pytest
from app.domain.matching_engine import calculate_overall_match, calculate_skill_gap
from app.domain.recommendation_engine import (
    determine_recommendation_priority,
    determine_recommendation_reason,
    generate_recommendations,
)


def test_calculate_skill_gap_boundaries():
    # Exact match
    r1 = calculate_skill_gap(required_level=4, current_level=4)
    assert r1["gap"] == 0
    assert r1["matched"] is True
    assert r1["status"] == "MATCHED"

    # Overqualified
    r2 = calculate_skill_gap(required_level=3, current_level=5)
    assert r2["gap"] == 0
    assert r2["matched"] is True
    assert r2["status"] == "MATCHED"

    # Underqualified
    r3 = calculate_skill_gap(required_level=4, current_level=2)
    assert r3["gap"] == 2
    assert r3["matched"] is False
    assert r3["status"] == "GAP"

    # Missing skill
    r4 = calculate_skill_gap(required_level=3, current_level=0)
    assert r4["gap"] == 3
    assert r4["matched"] is False
    assert r4["status"] == "GAP"


def test_overall_match_formula_weights_and_rounding():
    # Job requirements:
    # 1: req=4, mandatory=True (weight 2)
    # 2: req=3, mandatory=False (weight 1)
    reqs = [
        {"skill_id": 1, "required_level": 4, "mandatory": True},
        {"skill_id": 2, "required_level": 3, "mandatory": False},
    ]
    # Student: skill 1 = 3 (ratio 3/4 = 0.75), skill 2 = 3 (ratio 3/3 = 1.0)
    # Weighted sum: 2 * 0.75 + 1 * 1.0 = 1.5 + 1.0 = 2.5
    # Total weight: 2 + 1 = 3
    # 100 * 2.5 / 3 = 83.333... -> round = 83
    score, items = calculate_overall_match(reqs, {1: 3, 2: 3})
    assert score == 83
    assert len(items) == 2


def test_empty_requirements_returns_100():
    score, items = calculate_overall_match([], {1: 3})
    assert score == 100
    assert items == []


def test_source_example_benchmark():
    """Section 25 Source benchmark test:

    Student:
    Java = 4, MySQL = 4, Python = 3, React = 2, AWS = 1
    Job:
    Java = 4 (Mandatory)
    Spring Boot = 4 (Mandatory)
    React = 3 (Mandatory)
    MySQL = 3 (Mandatory)
    AWS = 2 (Optional)
    """
    skill_ids = {"Java": 1, "Spring Boot": 2, "React": 3, "MySQL": 4, "AWS": 5, "Python": 6}
    student_skills = {
        skill_ids["Java"]: 4,
        skill_ids["MySQL"]: 4,
        skill_ids["Python"]: 3,
        skill_ids["React"]: 2,
        skill_ids["AWS"]: 1,
    }

    job_requirements = [
        {"skill_id": skill_ids["Java"], "required_level": 4, "mandatory": True},
        {"skill_id": skill_ids["Spring Boot"], "required_level": 4, "mandatory": True},
        {"skill_id": skill_ids["React"], "required_level": 3, "mandatory": True},
        {"skill_id": skill_ids["MySQL"], "required_level": 3, "mandatory": True},
        {"skill_id": skill_ids["AWS"], "required_level": 2, "mandatory": False},
    ]

    score, items = calculate_overall_match(job_requirements, student_skills)
    items_by_id = {item["skill_id"]: item for item in items}

    # Verify gaps
    assert items_by_id[skill_ids["Java"]]["gap"] == 0
    assert items_by_id[skill_ids["Java"]]["status"] == "MATCHED"

    assert items_by_id[skill_ids["MySQL"]]["gap"] == 0
    assert items_by_id[skill_ids["MySQL"]]["status"] == "MATCHED"

    assert items_by_id[skill_ids["Spring Boot"]]["gap"] == 4
    assert items_by_id[skill_ids["Spring Boot"]]["status"] == "GAP"

    assert items_by_id[skill_ids["React"]]["gap"] == 1
    assert items_by_id[skill_ids["React"]]["status"] == "GAP"

    assert items_by_id[skill_ids["AWS"]]["gap"] == 1
    assert items_by_id[skill_ids["AWS"]]["status"] == "GAP"

    # Verify recommendations
    skill_names = {v: k for k, v in skill_ids.items()}
    recs = generate_recommendations("run-1", 10, 20, items, skill_names)

    # 3 gaps -> exactly 3 recommendations (Java and MySQL have gap 0 so no recommendation)
    assert len(recs) == 3

    # Ordering:
    # 1. Mandatory gaps first: Spring Boot (mandatory, gap 4), React (mandatory, gap 1)
    # 2. Optional gaps next: AWS (optional, gap 1)
    assert recs[0]["skill_name"] == "Spring Boot"
    assert recs[0]["priority"] == "HIGH"
    assert recs[0]["reason"] == "Mandatory job requirement"

    assert recs[1]["skill_name"] == "React"
    assert recs[1]["priority"] == "MEDIUM"
    assert recs[1]["reason"] == "Mandatory job requirement"

    assert recs[2]["skill_name"] == "AWS"
    assert recs[2]["priority"] == "LOW"
    assert recs[2]["reason"] == "Required supporting skill"
