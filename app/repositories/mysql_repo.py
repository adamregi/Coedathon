from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    AnalysisItemORM,
    AnalysisRunORM,
    ApplicationORM,
    JobORM,
    JobSkillORM,
    RecommendationORM,
    SkillORM,
    StudentORM,
    StudentSkillORM,
    UserORM,
)
from app.domain.models import (
    AnalysisItem,
    AnalysisRun,
    Application,
    ApplicationStatus,
    Job,
    JobSkill,
    Recommendation,
    RefreshToken,
    Role,
    SkillCatalog,
    StudentProfile,
    StudentSkill,
    User,
)
from app.domain.protocols import (
    ApplicationRepositoryProtocol,
    JobRepositoryProtocol,
    MatchingRepositoryProtocol,
    SkillRepositoryProtocol,
    StudentRepositoryProtocol,
    UserRepositoryProtocol,
)


class MySQLUserRepository(UserRepositoryProtocol):
    def __init__(self, db: Session):
        self.db = db
        # In-memory refresh token cache for fast rotation
        self._tokens: Dict[str, RefreshToken] = {}

    def create(self, user: User) -> User:
        orm = UserORM(
            email=user.email.lower(),
            hashed_password=user.hashed_password,
            full_name=user.full_name,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            is_active=user.is_active,
            created_at=user.created_at,
        )
        self.db.add(orm)
        self.db.commit()
        self.db.refresh(orm)
        user.id = orm.id
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        orm = self.db.get(UserORM, user_id)
        if not orm:
            return None
        return User(
            id=orm.id,
            email=orm.email,
            hashed_password=orm.hashed_password,
            full_name=orm.full_name,
            role=Role(orm.role),
            is_active=orm.is_active,
            created_at=orm.created_at,
        )

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(UserORM).where(func.lower(UserORM.email) == email.lower().strip())
        orm = self.db.execute(stmt).scalar_one_or_none()
        if not orm:
            return None
        return User(
            id=orm.id,
            email=orm.email,
            hashed_password=orm.hashed_password,
            full_name=orm.full_name,
            role=Role(orm.role),
            is_active=orm.is_active,
            created_at=orm.created_at,
        )

    def list_all(self, skip: int = 0, limit: int = 50) -> Tuple[List[User], int]:
        total = self.db.execute(select(func.count(UserORM.id))).scalar_one()
        stmt = select(UserORM).offset(skip).limit(limit)
        orms = self.db.execute(stmt).scalars().all()
        users = [
            User(
                id=o.id,
                email=o.email,
                hashed_password=o.hashed_password,
                full_name=o.full_name,
                role=Role(o.role),
                is_active=o.is_active,
                created_at=o.created_at,
            )
            for o in orms
        ]
        return users, total

    def save_refresh_token(self, token: RefreshToken) -> RefreshToken:
        self._tokens[token.token_hash] = token
        return token

    def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        return self._tokens.get(token_hash)

    def revoke_refresh_token(self, token_hash: str) -> bool:
        if token_hash in self._tokens:
            self._tokens[token_hash].is_revoked = True
            return True
        return False

    def revoke_family_tokens(self, family_id: str) -> int:
        count = 0
        for t in self._tokens.values():
            if t.family_id == family_id and not t.is_revoked:
                t.is_revoked = True
                count += 1
        return count


class MySQLStudentRepository(StudentRepositoryProtocol):
    def __init__(self, db: Session):
        self.db = db

    def _to_profile(self, orm: StudentORM) -> StudentProfile:
        skills = []
        if orm.skills:
            for s in orm.skills:
                skills.append(
                    StudentSkill(
                        id=s.id,
                        student_id=s.student_id,
                        skill_id=s.skill_id,
                        proficiency=s.proficiency,
                        skill_name=s.skill.name if s.skill else None,
                        category=s.skill.category if s.skill else None,
                    )
                )
        return StudentProfile(
            student_id=orm.student_id,
            name=orm.name,
            email=orm.email,
            user_id=orm.user_id,
            headline=orm.headline,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            skills=skills,
        )

    def create_student(self, student: StudentProfile) -> StudentProfile:
        orm = StudentORM(
            name=student.name,
            email=student.email.lower(),
            user_id=student.user_id,
            headline=student.headline,
            created_at=student.created_at,
            updated_at=student.updated_at,
        )
        self.db.add(orm)
        self.db.commit()
        self.db.refresh(orm)
        student.student_id = orm.student_id
        return student

    def get_student_by_id(self, student_id: int) -> Optional[StudentProfile]:
        orm = self.db.get(StudentORM, student_id)
        return self._to_profile(orm) if orm else None

    def get_student_by_user_id(self, user_id: int) -> Optional[StudentProfile]:
        stmt = select(StudentORM).where(StudentORM.user_id == user_id)
        orm = self.db.execute(stmt).scalar_one_or_none()
        return self._to_profile(orm) if orm else None

    def get_student_by_email(self, email: str) -> Optional[StudentProfile]:
        stmt = select(StudentORM).where(func.lower(StudentORM.email) == email.lower())
        orm = self.db.execute(stmt).scalar_one_or_none()
        return self._to_profile(orm) if orm else None

    def update_student(self, student: StudentProfile) -> StudentProfile:
        orm = self.db.get(StudentORM, student.student_id)
        if orm:
            orm.headline = student.headline
            orm.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(orm)
            return self._to_profile(orm)
        return student

    def list_students(self, skip: int = 0, limit: int = 50) -> Tuple[List[StudentProfile], int]:
        total = self.db.execute(select(func.count(StudentORM.student_id))).scalar_one()
        stmt = select(StudentORM).offset(skip).limit(limit)
        orms = self.db.execute(stmt).scalars().all()
        return [self._to_profile(o) for o in orms], total

    def upsert_skill(self, student_id: int, skill_id: int, proficiency: int) -> StudentSkill:
        stmt = select(StudentSkillORM).where(
            StudentSkillORM.student_id == student_id,
            StudentSkillORM.skill_id == skill_id,
        )
        orm = self.db.execute(stmt).scalar_one_or_none()
        if orm:
            orm.proficiency = proficiency
        else:
            orm = StudentSkillORM(
                student_id=student_id,
                skill_id=skill_id,
                proficiency=proficiency,
            )
            self.db.add(orm)
        self.db.commit()
        self.db.refresh(orm)

        skill = self.db.get(SkillORM, skill_id)
        return StudentSkill(
            id=orm.id,
            student_id=orm.student_id,
            skill_id=orm.skill_id,
            proficiency=orm.proficiency,
            skill_name=skill.name if skill else None,
            category=skill.category if skill else None,
        )

    def delete_skill(self, student_id: int, skill_id: int) -> bool:
        stmt = select(StudentSkillORM).where(
            StudentSkillORM.student_id == student_id,
            StudentSkillORM.skill_id == skill_id,
        )
        orm = self.db.execute(stmt).scalar_one_or_none()
        if orm:
            self.db.delete(orm)
            self.db.commit()
            return True
        return False

    def get_skills(self, student_id: int) -> List[StudentSkill]:
        stmt = select(StudentSkillORM).where(StudentSkillORM.student_id == student_id)
        orms = self.db.execute(stmt).scalars().all()
        results = []
        for o in orms:
            results.append(
                StudentSkill(
                    id=o.id,
                    student_id=o.student_id,
                    skill_id=o.skill_id,
                    proficiency=o.proficiency,
                    skill_name=o.skill.name if o.skill else None,
                    category=o.skill.category if o.skill else None,
                )
            )
        return results

    # Compatibility aliases
    create_profile = create_student
    get_profile_by_user_id = get_student_by_user_id
    get_profile_by_id = get_student_by_id
    update_profile = update_student
    list_profiles = list_students


class MySQLSkillRepository(SkillRepositoryProtocol):
    def __init__(self, db: Session):
        self.db = db

    def create(self, skill: SkillCatalog) -> SkillCatalog:
        orm = SkillORM(
            name=skill.name,
            normalized_name=skill.normalized_name.lower().strip(),
            category=skill.category,
            description=skill.description,
            created_at=skill.created_at,
        )
        self.db.add(orm)
        self.db.commit()
        self.db.refresh(orm)
        skill.id = orm.id
        return skill

    def get_by_id(self, skill_id: int) -> Optional[SkillCatalog]:
        orm = self.db.get(SkillORM, skill_id)
        if not orm:
            return None
        return SkillCatalog(
            id=orm.id,
            name=orm.name,
            normalized_name=orm.normalized_name,
            category=orm.category,
            description=orm.description,
            created_at=orm.created_at,
            updated_at=orm.created_at,
        )

    def get_by_normalized_name(self, normalized_name: str) -> Optional[SkillCatalog]:
        stmt = select(SkillORM).where(func.lower(SkillORM.normalized_name) == normalized_name.lower().strip())
        orm = self.db.execute(stmt).scalar_one_or_none()
        if not orm:
            return None
        return SkillCatalog(
            id=orm.id,
            name=orm.name,
            normalized_name=orm.normalized_name,
            category=orm.category,
            description=orm.description,
            created_at=orm.created_at,
            updated_at=orm.created_at,
        )

    def update(self, skill: SkillCatalog) -> SkillCatalog:
        orm = self.db.get(SkillORM, skill.id)
        if orm:
            orm.name = skill.name
            orm.normalized_name = skill.normalized_name.lower().strip()
            orm.category = skill.category
            orm.description = skill.description
            self.db.commit()
            self.db.refresh(orm)
        return skill

    def delete(self, skill_id: int) -> bool:
        orm = self.db.get(SkillORM, skill_id)
        if orm:
            self.db.delete(orm)
            self.db.commit()
            return True
        return False

    def list_all(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[SkillCatalog], int]:
        stmt = select(SkillORM)
        if category:
            stmt = stmt.where(func.lower(SkillORM.category) == category.lower().strip())
        if search:
            q = f"%{search.lower().strip()}%"
            stmt = stmt.where(func.lower(SkillORM.name).like(q))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.offset(skip).limit(limit)
        orms = self.db.execute(stmt).scalars().all()
        skills = [
            SkillCatalog(
                id=o.id,
                name=o.name,
                normalized_name=o.normalized_name,
                category=o.category,
                description=o.description,
                created_at=o.created_at,
                updated_at=o.created_at,
            )
            for o in orms
        ]
        return skills, total


class MySQLJobRepository(JobRepositoryProtocol):
    def __init__(self, db: Session):
        self.db = db

    def _to_job(self, orm: JobORM) -> Job:
        skills = []
        if orm.skills:
            for s in orm.skills:
                skills.append(
                    JobSkill(
                        id=s.id,
                        job_id=s.job_id,
                        skill_id=s.skill_id,
                        required_level=s.required_level,
                        mandatory=s.mandatory,
                        skill_name=s.skill.name if s.skill else None,
                        category=s.skill.category if s.skill else None,
                        created_at=s.created_at,
                    )
                )
        return Job(
            id=orm.id,
            employer_id=orm.employer_id,
            title=orm.title,
            company_name=orm.company_name,
            description=orm.description,
            department=orm.department,
            location=orm.location,
            salary_range=orm.salary_range,
            is_active=orm.is_active,
            created_at=orm.created_at,
            skills=skills,
        )

    def create_job(self, job: Job) -> Job:
        orm = JobORM(
            employer_id=job.employer_id,
            title=job.title,
            company_name=job.company_name,
            description=job.description,
            department=job.department,
            location=job.location,
            salary_range=job.salary_range,
            is_active=job.is_active,
            created_at=job.created_at,
        )
        self.db.add(orm)
        self.db.commit()
        self.db.refresh(orm)
        job.id = orm.id

        if job.skills:
            for s in job.skills:
                s_orm = JobSkillORM(
                    job_id=job.id,
                    skill_id=s.skill_id,
                    required_level=s.required_level,
                    mandatory=s.mandatory,
                )
                self.db.add(s_orm)
            self.db.commit()
            self.db.refresh(orm)

        return self._to_job(orm)

    def get_job_by_id(self, job_id: int) -> Optional[Job]:
        orm = self.db.get(JobORM, job_id)
        return self._to_job(orm) if orm else None

    def update_job(self, job: Job) -> Job:
        orm = self.db.get(JobORM, job.id)
        if orm:
            orm.title = job.title
            orm.company_name = job.company_name
            orm.description = job.description
            orm.department = job.department
            orm.location = job.location
            orm.salary_range = job.salary_range
            orm.is_active = job.is_active
            self.db.commit()
            self.db.refresh(orm)
            return self._to_job(orm)
        return job

    def delete_job(self, job_id: int) -> bool:
        orm = self.db.get(JobORM, job_id)
        if orm:
            self.db.delete(orm)
            self.db.commit()
            return True
        return False

    def list_jobs(
        self,
        employer_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Job], int]:
        stmt = select(JobORM)
        if employer_id is not None:
            stmt = stmt.where(JobORM.employer_id == employer_id)
        if is_active is not None:
            stmt = stmt.where(JobORM.is_active == is_active)
        if search:
            q = f"%{search.lower().strip()}%"
            stmt = stmt.where(
                func.lower(JobORM.title).like(q)
                | func.lower(JobORM.company_name).like(q)
                | func.lower(JobORM.description).like(q)
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.offset(skip).limit(limit)
        orms = self.db.execute(stmt).scalars().all()
        return [self._to_job(o) for o in orms], total

    def upsert_skill(
        self,
        job_id_or_skill: Any,
        skill_id_or_skill: Any = None,
        required_level: Optional[int] = None,
        mandatory: bool = True,
    ) -> JobSkill:
        if hasattr(job_id_or_skill, "job_id"):
            job_id = job_id_or_skill.job_id
            skill_id = job_id_or_skill.skill_id
            required_level = getattr(job_id_or_skill, "required_proficiency", None) or getattr(job_id_or_skill, "required_level", 1)
            mandatory = job_id_or_skill.mandatory
        elif hasattr(skill_id_or_skill, "skill_id"):
            job_id = job_id_or_skill
            skill_id = skill_id_or_skill.skill_id
            required_level = getattr(skill_id_or_skill, "required_proficiency", None) or getattr(skill_id_or_skill, "required_level", 1)
            mandatory = skill_id_or_skill.mandatory
        else:
            job_id = job_id_or_skill
            skill_id = skill_id_or_skill
            required_level = required_level or 1

        stmt = select(JobSkillORM).where(
            JobSkillORM.job_id == job_id,
            JobSkillORM.skill_id == skill_id,
        )
        orm = self.db.execute(stmt).scalar_one_or_none()
        if orm:
            orm.required_level = required_level
            orm.mandatory = mandatory
        else:
            orm = JobSkillORM(
                job_id=job_id,
                skill_id=skill_id,
                required_level=required_level,
                mandatory=mandatory,
            )
            self.db.add(orm)
        self.db.commit()
        self.db.refresh(orm)

        skill = self.db.get(SkillORM, skill_id)
        return JobSkill(
            id=orm.id,
            job_id=orm.job_id,
            skill_id=orm.skill_id,
            required_level=orm.required_level,
            mandatory=orm.mandatory,
            skill_name=skill.name if skill else None,
            category=skill.category if skill else None,
            created_at=orm.created_at,
        )

    def delete_skill(self, job_id: int, skill_id: int) -> bool:
        stmt = select(JobSkillORM).where(
            JobSkillORM.job_id == job_id,
            JobSkillORM.skill_id == skill_id,
        )
        orm = self.db.execute(stmt).scalar_one_or_none()
        if orm:
            self.db.delete(orm)
            self.db.commit()
            return True
        return False

    upsert_requirement = upsert_skill
    delete_requirement = delete_skill

    def get_skills(self, job_id: int) -> List[JobSkill]:
        stmt = select(JobSkillORM).where(JobSkillORM.job_id == job_id)
        orms = self.db.execute(stmt).scalars().all()
        return [
            JobSkill(
                id=o.id,
                job_id=o.job_id,
                skill_id=o.skill_id,
                required_level=o.required_level,
                mandatory=o.mandatory,
                skill_name=o.skill.name if o.skill else None,
                category=o.skill.category if o.skill else None,
                created_at=o.created_at,
            )
            for o in orms
        ]


class MySQLMatchingRepository(MatchingRepositoryProtocol):
    def __init__(self, db: Session):
        self.db = db

    def save_analysis(
        self, run: AnalysisRun, items: List[AnalysisItem], recs: List[Recommendation]
    ) -> AnalysisRun:
        run_orm = AnalysisRunORM(
            id=run.id,
            student_id=run.student_id,
            job_id=run.job_id,
            algorithm_version=run.algorithm_version,
            overall_match_percentage=run.overall_match_percentage,
            created_at=run.created_at,
        )
        self.db.add(run_orm)

        for it in items:
            item_orm = AnalysisItemORM(
                analysis_run_id=run.id,
                skill_id=it.skill_id,
                required_level=it.required_level,
                current_level=it.current_level,
                gap=it.gap,
                matched=it.matched,
                mandatory=it.mandatory,
            )
            self.db.add(item_orm)

        for rc in recs:
            rec_orm = RecommendationORM(
                student_id=run.student_id,
                job_id=run.job_id,
                skill_id=rc.skill_id,
                current_level=rc.current_level,
                target_level=rc.target_level,
                analysis_run_id=run.id,
                priority=rc.priority,
                reason=rc.reason,
                created_at=rc.created_at,
            )
            self.db.add(rec_orm)

        self.db.commit()
        self.db.refresh(run_orm)
        run.items = items
        run.recommendations = recs
        return run

    def get_analysis_run(self, run_id: str) -> Optional[AnalysisRun]:
        orm = self.db.get(AnalysisRunORM, run_id)
        if not orm:
            return None

        items = []
        for i in orm.items:
            items.append(
                AnalysisItem(
                    id=i.id,
                    analysis_run_id=i.analysis_run_id,
                    skill_id=i.skill_id,
                    required_level=i.required_level,
                    current_level=i.current_level,
                    gap=i.gap,
                    matched=i.matched,
                    mandatory=i.mandatory,
                    skill_name=i.skill.name if i.skill else None,
                    category=i.skill.category if i.skill else None,
                )
            )

        recs = []
        for r in orm.recommendations:
            recs.append(
                Recommendation(
                    id=r.id,
                    student_id=r.student_id,
                    job_id=r.job_id,
                    skill_id=r.skill_id,
                    current_level=r.current_level,
                    target_level=r.target_level,
                    analysis_run_id=r.analysis_run_id,
                    priority=r.priority,
                    reason=r.reason,
                    skill_name=r.skill.name if r.skill else None,
                    created_at=r.created_at,
                )
            )

        return AnalysisRun(
            id=orm.id,
            student_id=orm.student_id,
            job_id=orm.job_id,
            algorithm_version=orm.algorithm_version,
            overall_match_percentage=orm.overall_match_percentage,
            created_at=orm.created_at,
            items=items,
            recommendations=recs,
        )

    def get_latest_run(self, student_id: int, job_id: int) -> Optional[AnalysisRun]:
        stmt = (
            select(AnalysisRunORM)
            .where(AnalysisRunORM.student_id == student_id, AnalysisRunORM.job_id == job_id)
            .order_by(AnalysisRunORM.created_at.desc())
        )
        orm = self.db.execute(stmt).scalars().first()
        if not orm:
            return None
        return self.get_analysis_run(orm.id)

    def list_runs_for_student(
        self, student_id: int, skip: int = 0, limit: int = 50
    ) -> Tuple[List[AnalysisRun], int]:
        stmt = select(AnalysisRunORM).where(AnalysisRunORM.student_id == student_id)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(AnalysisRunORM.created_at.desc()).offset(skip).limit(limit)
        orms = self.db.execute(stmt).scalars().all()
        return [self.get_analysis_run(o.id) for o in orms], total

    def list_recommendations(self, student_id: int, job_id: int) -> List[Recommendation]:
        stmt = (
            select(RecommendationORM)
            .where(
                RecommendationORM.student_id == student_id,
                RecommendationORM.job_id == job_id,
            )
            .order_by(RecommendationORM.created_at.desc())
        )
        orms = self.db.execute(stmt).scalars().all()
        recs = []
        for r in orms:
            recs.append(
                Recommendation(
                    id=r.id,
                    student_id=r.student_id,
                    job_id=r.job_id,
                    skill_id=r.skill_id,
                    current_level=r.current_level,
                    target_level=r.target_level,
                    analysis_run_id=r.analysis_run_id,
                    priority=r.priority,
                    reason=r.reason,
                    skill_name=r.skill.name if r.skill else None,
                    created_at=r.created_at,
                )
            )
        return recs

    def list_candidate_runs_for_job(
        self, job_id: int, skip: int = 0, limit: int = 50
    ) -> Tuple[List[AnalysisRun], int]:
        stmt = select(AnalysisRunORM).where(AnalysisRunORM.job_id == job_id)
        orms = self.db.execute(stmt).scalars().all()

        # Group by student_id, keeping latest run
        student_latest: Dict[int, AnalysisRunORM] = {}
        for o in sorted(orms, key=lambda x: x.created_at):
            student_latest[o.student_id] = o

        candidates = [self.get_analysis_run(o.id) for o in student_latest.values()]
        candidates.sort(key=lambda r: (r.overall_match_percentage, r.created_at), reverse=True)
        total = len(candidates)
        return candidates[skip : skip + limit], total


class MySQLApplicationRepository(ApplicationRepositoryProtocol):
    def __init__(self, db: Session):
        self.db = db

    def create_application(self, app: Application) -> Application:
        orm = ApplicationORM(
            student_id=app.student_id,
            job_id=app.job_id,
            status=app.status.value if hasattr(app.status, "value") else str(app.status),
            match_percentage_snapshot=app.match_percentage_snapshot,
            created_at=app.created_at,
        )
        self.db.add(orm)
        self.db.commit()
        self.db.refresh(orm)
        app.id = orm.id
        return app

    def get_application_by_id(self, app_id: int) -> Optional[Application]:
        orm = self.db.get(ApplicationORM, app_id)
        if not orm:
            return None
        return Application(
            id=orm.id,
            student_id=orm.student_id,
            job_id=orm.job_id,
            status=ApplicationStatus(orm.status),
            match_percentage_snapshot=orm.match_percentage_snapshot,
            created_at=orm.created_at,
        )

    def get_active_application(self, student_id: int, job_id: int) -> Optional[Application]:
        stmt = select(ApplicationORM).where(
            ApplicationORM.student_id == student_id,
            ApplicationORM.job_id == job_id,
            ApplicationORM.status.notin_(["withdrawn", "closed"]),
        )
        orm = self.db.execute(stmt).scalars().first()
        if not orm:
            return None
        return Application(
            id=orm.id,
            student_id=orm.student_id,
            job_id=orm.job_id,
            status=ApplicationStatus(orm.status),
            match_percentage_snapshot=orm.match_percentage_snapshot,
            created_at=orm.created_at,
        )

    def update_application(self, app: Application) -> Application:
        orm = self.db.get(ApplicationORM, app.id)
        if orm:
            orm.status = app.status.value if hasattr(app.status, "value") else str(app.status)
            self.db.commit()
            self.db.refresh(orm)
        return app

    def list_applications(
        self,
        student_id: Optional[int] = None,
        job_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Application], int]:
        stmt = select(ApplicationORM)
        if student_id is not None:
            stmt = stmt.where(ApplicationORM.student_id == student_id)
        if job_id is not None:
            stmt = stmt.where(ApplicationORM.job_id == job_id)
        if status is not None:
            stmt = stmt.where(ApplicationORM.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(ApplicationORM.created_at.desc()).offset(skip).limit(limit)
        orms = self.db.execute(stmt).scalars().all()
        apps = [
            Application(
                id=o.id,
                student_id=o.student_id,
                job_id=o.job_id,
                status=ApplicationStatus(o.status),
                match_percentage_snapshot=o.match_percentage_snapshot,
                created_at=o.created_at,
            )
            for o in orms
        ]
        return apps, total
