from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class Role(str, Enum):
    ADMIN = "admin"
    STUDENT = "student"
    EMPLOYER = "employer"


class ApplicationStatus(str, Enum):
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    CLOSED = "closed"
    WITHDRAWN = "withdrawn"


@dataclass
class User:
    id: int
    email: str
    hashed_password: str
    full_name: str
    role: Role = Role.STUDENT
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RefreshToken:
    id: int
    user_id: int
    token_hash: str
    family_id: str
    is_revoked: bool = False
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SkillCatalog:
    id: int
    name: str
    normalized_name: str
    category: str
    description: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))


class StudentSkill:
    def __init__(
        self,
        id: int = 0,
        student_id: int = 0,
        skill_id: int = 0,
        proficiency: int = 1,
        skill_name: Optional[str] = None,
        category: Optional[str] = None,
        student_profile_id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        **kwargs,
    ):
        self.id = id
        self.student_id = student_id if student_id else (student_profile_id or 0)
        self.skill_id = skill_id
        self.proficiency = proficiency
        self.skill_name = skill_name
        self.category = category
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    @property
    def student_profile_id(self) -> int:
        return self.student_id

    @student_profile_id.setter
    def student_profile_id(self, val: int):
        self.student_id = val


class StudentProfile:
    def __init__(
        self,
        student_id: Optional[int] = None,
        name: str = "Student",
        email: str = "",
        user_id: int = 0,
        headline: Optional[str] = None,
        skills: Optional[List[StudentSkill]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        id: Optional[int] = None,
        **kwargs,
    ):
        self.student_id = student_id if student_id is not None else (id or 0)
        self.name = name
        self.email = email
        self.user_id = user_id
        self.headline = headline
        self.skills = skills if skills is not None else []
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    @property
    def id(self) -> int:
        return self.student_id

    @id.setter
    def id(self, val: int):
        self.student_id = val


class JobSkill:
    def __init__(
        self,
        id: int = 0,
        job_id: int = 0,
        skill_id: int = 0,
        required_level: int = 1,
        mandatory: bool = True,
        skill_name: Optional[str] = None,
        category: Optional[str] = None,
        required_proficiency: Optional[int] = None,
        created_at: Optional[datetime] = None,
        **kwargs,
    ):
        self.id = id
        self.job_id = job_id
        self.skill_id = skill_id
        self.required_level = required_level if required_proficiency is None else required_proficiency
        self.mandatory = mandatory
        self.skill_name = skill_name
        self.category = category
        self.created_at = created_at or datetime.now(timezone.utc)

    @property
    def required_proficiency(self) -> int:
        return self.required_level

    @required_proficiency.setter
    def required_proficiency(self, val: int):
        self.required_level = val


# Alias for backwards compatibility
JobRequirement = JobSkill


class Job:
    def __init__(
        self,
        id: int = 0,
        employer_id: Optional[int] = None,
        title: str = "",
        company_name: str = "",
        description: str = "",
        department: Optional[str] = None,
        location: Optional[str] = None,
        salary_range: Optional[str] = None,
        is_active: bool = True,
        skills: Optional[List[JobSkill]] = None,
        requirements: Optional[List[JobSkill]] = None,
        created_at: Optional[datetime] = None,
        **kwargs,
    ):
        self.id = id
        self.employer_id = employer_id
        self.title = title
        self.company_name = company_name
        self.description = description
        self.department = department
        self.location = location
        self.salary_range = salary_range
        self.is_active = is_active
        self.skills = skills if skills is not None else (requirements or [])
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = kwargs.get("updated_at", self.created_at)

    @property
    def requirements(self) -> List[JobSkill]:
        return self.skills

    @requirements.setter
    def requirements(self, val: List[JobSkill]):
        self.skills = val


@dataclass
class AnalysisItem:
    id: int
    analysis_run_id: str
    skill_id: int
    required_level: int
    current_level: int
    gap: int
    matched: bool
    mandatory: bool
    skill_name: Optional[str] = None
    category: Optional[str] = None


# Compatibility alias
SkillMatchResult = AnalysisItem


@dataclass
class Recommendation:
    id: int
    student_id: int
    job_id: int
    skill_id: int
    current_level: int
    target_level: int
    analysis_run_id: str
    priority: str  # HIGH, MEDIUM, LOW
    reason: str
    skill_name: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def gap(self) -> int:
        return max(self.target_level - self.current_level, 0)

    @property
    def suggested_action(self) -> str:
        return f"Upskill {self.skill_name or f'Skill #{self.skill_id}'} from level {self.current_level} to {self.target_level}"


@dataclass
class AnalysisRun:
    id: str  # UUID
    student_id: int
    job_id: int
    algorithm_version: str = "v1.0"
    overall_match_percentage: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    items: List[AnalysisItem] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)

    @property
    def skill_results(self) -> List[AnalysisItem]:
        return self.items

    @skill_results.setter
    def skill_results(self, val: List[AnalysisItem]):
        self.items = val

    @property
    def raw_snapshot(self) -> Dict[str, Any]:
        return {
            "analysis_run_id": self.id,
            "student_id": self.student_id,
            "job_id": self.job_id,
            "overall_match_percentage": self.overall_match_percentage,
            "algorithm_version": self.algorithm_version,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Application:
    id: int
    student_id: int
    job_id: int
    status: ApplicationStatus
    match_percentage_snapshot: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
