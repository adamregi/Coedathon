from typing import Any, Dict, List
from pydantic import BaseModel


class SkillGapMetric(BaseModel):
    skill_name: str
    category: str
    count: int
    avg_gap: float


class StudentDashboardRead(BaseModel):
    total_applications: int
    active_applications: int
    average_match_percentage: float
    top_skill_gaps: List[SkillGapMetric]
    recent_analyses: List[Dict[str, Any]]


class EmployerDashboardRead(BaseModel):
    total_jobs: int
    active_jobs: int
    total_candidates: int
    average_candidate_match: float
    top_skill_gaps: List[SkillGapMetric]
    recent_applications: List[Dict[str, Any]]


class AdminDashboardRead(BaseModel):
    total_users: int
    total_students: int
    total_employers: int
    total_active_jobs: int
    total_applications: int
    platform_average_match: float
    top_demanded_skills: List[Dict[str, Any]]
