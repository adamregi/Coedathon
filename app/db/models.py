from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="student", nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    student: Mapped[Optional["StudentORM"]] = relationship(back_populates="user", uselist=False)
    jobs: Mapped[List["JobORM"]] = relationship(back_populates="employer")


class StudentORM(Base):
    __tablename__ = "students"

    student_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    headline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["UserORM"] = relationship(back_populates="student")
    skills: Mapped[List["StudentSkillORM"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    applications: Mapped[List["ApplicationORM"]] = relationship(back_populates="student")


class SkillORM(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )


class StudentSkillORM(Base):
    __tablename__ = "student_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    proficiency: Mapped[int] = mapped_column(Integer, nullable=False)

    student: Mapped["StudentORM"] = relationship(back_populates="skills")
    skill: Mapped["SkillORM"] = relationship()

    __table_args__ = (
        UniqueConstraint("student_id", "skill_id", name="uq_student_skill"),
        CheckConstraint("proficiency >= 1 AND proficiency <= 5", name="ck_proficiency_range"),
        Index("ix_student_skill_lookup", "student_id", "skill_id"),
    )


class JobORM(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    salary_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    employer: Mapped[Optional["UserORM"]] = relationship(back_populates="jobs")
    skills: Mapped[List["JobSkillORM"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    applications: Mapped[List["ApplicationORM"]] = relationship(back_populates="job")


class JobSkillORM(Base):
    __tablename__ = "job_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    required_level: Mapped[int] = mapped_column(Integer, nullable=False)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    job: Mapped["JobORM"] = relationship(back_populates="skills")
    skill: Mapped["SkillORM"] = relationship()

    __table_args__ = (
        UniqueConstraint("job_id", "skill_id", name="uq_job_skill"),
        CheckConstraint("required_level >= 1 AND required_level <= 5", name="ck_required_level_range"),
        Index("ix_job_skill_lookup", "job_id", "skill_id"),
    )


class AnalysisRunORM(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    algorithm_version: Mapped[str] = mapped_column(String(20), default="v1.0", nullable=False)
    overall_match_percentage: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    items: Mapped[List["AnalysisItemORM"]] = relationship(back_populates="analysis_run", cascade="all, delete-orphan")
    recommendations: Mapped[List["RecommendationORM"]] = relationship(
        back_populates="analysis_run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_student_job_analysis_created", "student_id", "job_id", "created_at"),
    )


class AnalysisItemORM(Base):
    __tablename__ = "analysis_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    required_level: Mapped[int] = mapped_column(Integer, nullable=False)
    current_level: Mapped[int] = mapped_column(Integer, nullable=False)
    gap: Mapped[int] = mapped_column(Integer, nullable=False)
    matched: Mapped[bool] = mapped_column(Boolean, nullable=False)
    mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False)

    analysis_run: Mapped["AnalysisRunORM"] = relationship(back_populates="items")
    skill: Mapped["SkillORM"] = relationship()


class RecommendationORM(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    current_level: Mapped[int] = mapped_column(Integer, nullable=False)
    target_level: Mapped[int] = mapped_column(Integer, nullable=False)
    analysis_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    priority: Mapped[str] = mapped_column(String(20), nullable=False)  # HIGH, MEDIUM, LOW
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    analysis_run: Mapped["AnalysisRunORM"] = relationship(back_populates="recommendations")
    skill: Mapped["SkillORM"] = relationship()

    __table_args__ = (
        Index("ix_rec_student_job", "student_id", "job_id"),
    )


class ApplicationORM(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="submitted", nullable=False, index=True)
    match_percentage_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    student: Mapped["StudentORM"] = relationship(back_populates="applications")
    job: Mapped["JobORM"] = relationship(back_populates="applications")

    __table_args__ = (
        Index("ix_app_student_job_status", "student_id", "job_id", "status"),
    )
