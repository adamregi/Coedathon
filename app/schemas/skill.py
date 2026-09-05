import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


def normalize_skill_name(raw_name: str) -> str:
    """Trim leading/trailing whitespace and collapse internal whitespace sequences to a single space."""
    return re.sub(r"\s+", " ", raw_name.strip())


class SkillCatalogCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        cleaned = normalize_skill_name(v)
        if not cleaned:
            raise ValueError("Skill name cannot be empty or only whitespace")
        return cleaned

    @field_validator("category")
    @classmethod
    def clean_category(cls, v: str) -> str:
        cleaned = normalize_skill_name(v)
        if not cleaned:
            raise ValueError("Category cannot be empty or only whitespace")
        return cleaned


class SkillCatalogUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = normalize_skill_name(v)
            if not cleaned:
                raise ValueError("Skill name cannot be empty")
            return cleaned
        return v

    @field_validator("category")
    @classmethod
    def clean_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = normalize_skill_name(v)
            if not cleaned:
                raise ValueError("Category cannot be empty")
            return cleaned
        return v


class SkillCatalogRead(BaseModel):
    id: int
    name: str
    normalized_name: str
    category: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
