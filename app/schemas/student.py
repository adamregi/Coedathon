from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class StudentSkillCreate(BaseModel):
    skill_id: int
    proficiency: int = Field(..., ge=1, le=5, description="Proficiency level between 1 and 5")


class StudentSkillUpdate(BaseModel):
    proficiency: int = Field(..., ge=1, le=5, description="Proficiency level between 1 and 5")


class StudentSkillRead(BaseModel):
    id: int
    student_profile_id: int
    skill_id: int
    skill_name: Optional[str] = None
    category: Optional[str] = None
    proficiency: int
    created_at: datetime
    updated_at: datetime


class StudentProfileCreate(BaseModel):
    headline: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    education: Optional[str] = Field(None, max_length=255)
    graduation_year: Optional[int] = Field(None, ge=1900, le=2100)


class StudentProfileUpdate(BaseModel):
    headline: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    education: Optional[str] = Field(None, max_length=255)
    graduation_year: Optional[int] = Field(None, ge=1900, le=2100)


class StudentProfileRead(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    education: Optional[str] = None
    graduation_year: Optional[int] = None
    skills: List[StudentSkillRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
