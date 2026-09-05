from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class JobRequirementUpsert(BaseModel):
    skill_id: int
    required_proficiency: int = Field(..., ge=1, le=5, description="Required proficiency between 1 and 5")
    mandatory: bool = Field(default=True, description="Whether this requirement is mandatory (weight 2) or optional (weight 1)")


class JobRequirementRead(BaseModel):
    id: int
    job_id: int
    skill_id: int
    skill_name: Optional[str] = None
    category: Optional[str] = None
    required_proficiency: int
    mandatory: bool
    created_at: datetime


class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    company_name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    department: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    salary_range: Optional[str] = Field(None, max_length=100)
    is_active: bool = True
    requirements: List[JobRequirementUpsert] = Field(default_factory=list)


class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    department: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    salary_range: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class JobRead(BaseModel):
    id: int
    employer_id: int
    title: str
    company_name: str
    description: str
    department: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    is_active: bool
    requirements: List[JobRequirementRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
