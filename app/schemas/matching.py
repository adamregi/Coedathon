from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic_core import core_schema


class PriorityStr(str):
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.upper() == other.upper()
        return super().__eq__(other)

    def __hash__(self) -> int:
        return hash(self.upper())

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.no_info_after_validator_function(
            lambda v: cls(str(v).upper()),
            core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )


class SkillMatchResultRead(BaseModel):
    skill_id: int
    skill_name: str
    category: str
    required_proficiency: int
    current_proficiency: int
    mandatory: bool
    gap: int
    matched: bool


class RecommendationRead(BaseModel):
    id: int
    analysis_run_id: str
    skill_id: int
    skill_name: str
    suggested_action: str
    priority: PriorityStr  # "HIGH", "MEDIUM", "LOW"
    gap: int
    reason: str
    resource_url: Optional[str] = None
    created_at: datetime


class AnalysisRunRead(BaseModel):
    id: str
    student_id: int
    job_id: int
    algorithm_version: str = "v1.0"
    overall_match_percentage: int
    skill_results: List[SkillMatchResultRead]
    recommendations: List[RecommendationRead] = []
    raw_snapshot: Dict[str, Any]
    created_at: datetime


class StudentMatchRequest(BaseModel):
    job_id: int


class CandidateSkillSummary(BaseModel):
    skill_id: int
    skill_name: str
    category: Optional[str] = None
    proficiency: int


class CandidateRankingItemRead(BaseModel):
    student_id: int
    student_name: str
    student_email: str
    overall_match_percentage: int
    analysis_run_id: str
    calculated_at: datetime
    headline: Optional[str] = None
    skills: List[CandidateSkillSummary] = Field(default_factory=list)
