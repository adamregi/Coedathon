# Deferred Persistence & Migration Blueprint

This document specifies the target relational schema, SQLAlchemy 2.0 declarative mappings, indexing strategy, and Alembic migration sequence for when live MySQL database persistence is integrated.

---

## 1. Database & Engine Configuration

- **Target Engine**: MySQL 8.0+ (InnoDB engine, `utf8mb4_unicode_ci` collation).
- **Driver**: `asyncmy` or `aiomysql` with SQLAlchemy 2.0 AsyncEngine.
- **Connection URL**: `mysql+asyncmy://<user>:<password>@<host>:<port>/<dbname>?charset=utf8mb4`

---

## 2. Relational Schema & SQLAlchemy Declarative Models

```python
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Boolean, Float, Text, DateTime, ForeignKey,
    UniqueConstraint, Index, Enum as SQLEnum
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from app.domain.models import Role, ApplicationStatus

class Base(DeclarativeBase):
    pass

class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(SQLEnum(Role, native_enum=False), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    student_profile: Mapped[Optional["StudentProfileORM"]] = relationship(back_populates="user", uselist=False)
    jobs: Mapped[List["JobORM"]] = relationship(back_populates="employer")
    refresh_tokens: Mapped[List["RefreshTokenORM"]] = relationship(back_populates="user")


class RefreshTokenORM(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    family_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["UserORM"] = relationship(back_populates="refresh_tokens")


class SkillCatalogORM(Base):
    __tablename__ = "skill_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class StudentProfileORM(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    headline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    education: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    graduation_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user: Mapped["UserORM"] = relationship(back_populates="student_profile")
    skills: Mapped[List["StudentSkillORM"]] = relationship(back_populates="student_profile", cascade="all, delete-orphan")


class StudentSkillORM(Base):
    __tablename__ = "student_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skill_catalog.id", ondelete="RESTRICT"), nullable=False)
    proficiency: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 to 5
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    student_profile: Mapped["StudentProfileORM"] = relationship(back_populates="skills")
    skill: Mapped["SkillCatalogORM"] = relationship()

    __table_args__ = (
        UniqueConstraint("student_profile_id", "skill_id", name="uq_student_skill"),
        Index("ix_student_skill_lookup", "student_profile_id", "skill_id"),
    )


class JobORM(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    salary_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    employer: Mapped["UserORM"] = relationship(back_populates="jobs")
    requirements: Mapped[List["JobRequirementORM"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class JobRequirementORM(Base):
    __tablename__ = "job_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skill_catalog.id", ondelete="RESTRICT"), nullable=False)
    required_proficiency: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 to 5
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    job: Mapped["JobORM"] = relationship(back_populates="requirements")
    skill: Mapped["SkillCatalogORM"] = relationship()

    __table_args__ = (
        UniqueConstraint("job_id", "skill_id", name="uq_job_skill_requirement"),
        Index("ix_job_req_lookup", "job_id", "skill_id"),
    )


class AnalysisRunORM(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    algorithm_version: Mapped[str] = mapped_column(String(20), default="v1.0", nullable=False)
    overall_match_percentage: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON input snapshot
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    recommendations: Mapped[List["RecommendationORM"]] = relationship(back_populates="analysis_run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_student_job_analysis", "student_id", "job_id", "created_at"),
    )


class RecommendationORM(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skill_catalog.id", ondelete="RESTRICT"), nullable=False)
    suggested_action: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)  # high, medium, low
    gap: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    resource_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    analysis_run: Mapped["AnalysisRunORM"] = relationship(back_populates="recommendations")


class ApplicationORM(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[ApplicationStatus] = mapped_column(SQLEnum(ApplicationStatus, native_enum=False), default=ApplicationStatus.SUBMITTED, nullable=False, index=True)
    match_percentage_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_active_application", "student_id", "job_id", "status"),
    )


class AuditEventORM(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    actor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    details_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
```

---

## 3. Alembic Migration Sequence

When live database persistence is enabled, the migrations should execute in this strict chronological sequence:

1. **001_initial_users_and_tokens**:
   - Create `users` table with email index, password hash, role enum, and timestamps.
   - Create `refresh_tokens` table with FK to `users.id`, `token_hash`, `family_id`, and `is_revoked`.

2. **002_skill_catalog_and_students**:
   - Create `skill_catalog` table with unique constraint on `normalized_name` and category index.
   - Create `student_profiles` table with 1-to-1 link to `users.id`.
   - Create `student_skills` with compound unique constraint `(student_profile_id, skill_id)` and proficiency check constraint (`1 <= proficiency <= 5`).

3. **003_jobs_and_requirements**:
   - Create `jobs` table linked to `users.id` (employers), with title, department, active status.
   - Create `job_requirements` table with compound unique constraint `(job_id, skill_id)` and mandatory flag.

4. **004_matching_and_recommendations**:
   - Create `analysis_runs` table with UUID PK, immutable snapshot JSON, overall percentage, and foreign keys.
   - Create `recommendations` table linked to `analysis_runs.id`.

5. **005_applications_and_audit**:
   - Create `applications` table with status state tracking and snapshot score.
   - Create `audit_events` append-only table for compliance logging.
