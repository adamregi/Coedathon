from datetime import datetime, timezone
import threading
from typing import Any, Dict, List, Optional, Tuple
from app.domain.models import (
    AnalysisRun,
    Application,
    ApplicationStatus,
    Job,
    JobRequirement,
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


class InMemoryUserRepository(UserRepositoryProtocol):
    def __init__(self):
        self._lock = threading.RLock()
        self._users: Dict[int, User] = {}
        self._email_index: Dict[str, int] = {}
        self._refresh_tokens: Dict[str, RefreshToken] = {}  # key: token_hash
        self._next_id = 1
        self._next_token_id = 1

    def create(self, user: User) -> User:
        with self._lock:
            user.id = self._next_id
            self._next_id += 1
            now = datetime.now(timezone.utc)
            user.created_at = now
            user.updated_at = now
            self._users[user.id] = user
            self._email_index[user.email.lower()] = user.id
            return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        with self._lock:
            return self._users.get(user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        with self._lock:
            user_id = self._email_index.get(email.lower())
            return self._users.get(user_id) if user_id else None

    def list_all(self, skip: int = 0, limit: int = 50) -> Tuple[List[User], int]:
        with self._lock:
            all_users = list(self._users.values())
            total = len(all_users)
            return all_users[skip : skip + limit], total

    def save_refresh_token(self, token: RefreshToken) -> RefreshToken:
        with self._lock:
            token.id = self._next_token_id
            self._next_token_id += 1
            token.created_at = datetime.now(timezone.utc)
            self._refresh_tokens[token.token_hash] = token
            return token

    def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        with self._lock:
            return self._refresh_tokens.get(token_hash)

    def revoke_refresh_token(self, token_hash: str) -> bool:
        with self._lock:
            if token_hash in self._refresh_tokens:
                self._refresh_tokens[token_hash].is_revoked = True
                return True
            return False

    def revoke_family_tokens(self, family_id: str) -> int:
        with self._lock:
            count = 0
            for token in self._refresh_tokens.values():
                if token.family_id == family_id and not token.is_revoked:
                    token.is_revoked = True
                    count += 1
            return count


class InMemorySkillRepository(SkillRepositoryProtocol):
    def __init__(self):
        self._lock = threading.RLock()
        self._skills: Dict[int, SkillCatalog] = {}
        self._normalized_index: Dict[str, int] = {}
        self._next_id = 1

    def create(self, skill: SkillCatalog) -> SkillCatalog:
        with self._lock:
            skill.id = self._next_id
            self._next_id += 1
            now = datetime.now(timezone.utc)
            skill.created_at = now
            skill.updated_at = now
            self._skills[skill.id] = skill
            self._normalized_index[skill.normalized_name.lower()] = skill.id
            return skill

    def get_by_id(self, skill_id: int) -> Optional[SkillCatalog]:
        with self._lock:
            return self._skills.get(skill_id)

    def get_by_normalized_name(self, normalized_name: str) -> Optional[SkillCatalog]:
        with self._lock:
            skill_id = self._normalized_index.get(normalized_name.lower())
            return self._skills.get(skill_id) if skill_id else None

    def update(self, skill: SkillCatalog) -> SkillCatalog:
        with self._lock:
            skill.updated_at = datetime.now(timezone.utc)
            self._skills[skill.id] = skill
            self._normalized_index[skill.normalized_name.lower()] = skill.id
            return skill

    def delete(self, skill_id: int) -> bool:
        with self._lock:
            skill = self._skills.pop(skill_id, None)
            if skill:
                self._normalized_index.pop(skill.normalized_name.lower(), None)
                return True
            return False

    def list_all(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[SkillCatalog], int]:
        with self._lock:
            results = list(self._skills.values())
            if category:
                results = [s for s in results if s.category.lower() == category.lower()]
            if search:
                query = search.lower()
                results = [
                    s for s in results
                    if query in s.name.lower() or (s.description and query in s.description.lower())
                ]
            total = len(results)
            return results[skip : skip + limit], total


class InMemoryStudentRepository(StudentRepositoryProtocol):
    def __init__(self):
        self._lock = threading.RLock()
        self._profiles: Dict[int, StudentProfile] = {}  # key: profile_id
        self._user_to_profile: Dict[int, int] = {}      # key: user_id -> profile_id
        self._skills: Dict[int, List[StudentSkill]] = {} # key: profile_id -> list
        self._next_profile_id = 1
        self._next_skill_id = 1

    def create_profile(self, profile: StudentProfile) -> StudentProfile:
        with self._lock:
            profile.id = self._next_profile_id
            self._next_profile_id += 1
            now = datetime.now(timezone.utc)
            profile.created_at = now
            profile.updated_at = now
            self._profiles[profile.id] = profile
            self._user_to_profile[profile.user_id] = profile.id
            self._skills[profile.id] = []
            return profile

    def get_profile_by_user_id(self, user_id: int) -> Optional[StudentProfile]:
        with self._lock:
            profile_id = self._user_to_profile.get(user_id)
            if not profile_id:
                return None
            profile = self._profiles.get(profile_id)
            if profile:
                profile.skills = list(self._skills.get(profile_id, []))
            return profile

    def get_profile_by_id(self, profile_id: int) -> Optional[StudentProfile]:
        with self._lock:
            profile = self._profiles.get(profile_id)
            if profile:
                profile.skills = list(self._skills.get(profile_id, []))
            return profile

    def update_profile(self, profile: StudentProfile) -> StudentProfile:
        with self._lock:
            profile.updated_at = datetime.now(timezone.utc)
            self._profiles[profile.id] = profile
            profile.skills = list(self._skills.get(profile.id, []))
            return profile

    def list_profiles(self, skip: int = 0, limit: int = 50) -> Tuple[List[StudentProfile], int]:
        with self._lock:
            results = []
            for p in self._profiles.values():
                p.skills = list(self._skills.get(p.id, []))
                results.append(p)
            total = len(results)
            return results[skip : skip + limit], total

    # Canonical student repository methods
    create_student = create_profile
    get_student_by_id = get_profile_by_id
    get_student_by_user_id = get_profile_by_user_id

    def get_student_by_email(self, email: str) -> Optional[StudentProfile]:
        with self._lock:
            for p in self._profiles.values():
                if p.email and p.email.lower() == email.lower():
                    p.skills = list(self._skills.get(p.id, []))
                    return p
            return None

    update_student = update_profile
    list_students = list_profiles

    def upsert_skill(self, profile_id: int, skill_id_or_skill: Any, proficiency: Optional[int] = None) -> StudentSkill:
        with self._lock:
            if isinstance(skill_id_or_skill, StudentSkill):
                skill = skill_id_or_skill
            else:
                skill = StudentSkill(
                    id=0,
                    student_id=profile_id,
                    skill_id=skill_id_or_skill,
                    proficiency=proficiency or 1,
                )

            existing_skills = self._skills.setdefault(profile_id, [])
            for s in existing_skills:
                if s.skill_id == skill.skill_id:
                    s.proficiency = skill.proficiency
                    return s

            skill.id = self._next_skill_id
            self._next_skill_id += 1
            skill.student_id = profile_id
            existing_skills.append(skill)
            return skill

    def delete_skill(self, profile_id: int, skill_id: int) -> bool:
        with self._lock:
            skills = self._skills.get(profile_id, [])
            initial_len = len(skills)
            self._skills[profile_id] = [s for s in skills if s.skill_id != skill_id]
            return len(self._skills[profile_id]) < initial_len

    def get_skills(self, profile_id: int) -> List[StudentSkill]:
        with self._lock:
            return list(self._skills.get(profile_id, []))


class InMemoryJobRepository(JobRepositoryProtocol):
    def __init__(self):
        self._lock = threading.RLock()
        self._jobs: Dict[int, Job] = {}
        self._skills: Dict[int, List[JobSkill]] = {}  # key: job_id -> list
        self._next_job_id = 1
        self._next_req_id = 1

    def create_job(self, job: Job) -> Job:
        with self._lock:
            job.id = self._next_job_id
            self._next_job_id += 1
            now = datetime.now(timezone.utc)
            job.created_at = now
            self._jobs[job.id] = job
            self._skills[job.id] = []
            if job.skills:
                for req in job.skills:
                    req.id = self._next_req_id
                    self._next_req_id += 1
                    req.job_id = job.id
                    req.created_at = now
                    self._skills[job.id].append(req)
            job.skills = list(self._skills[job.id])
            return job

    def get_job_by_id(self, job_id: int) -> Optional[Job]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.skills = list(self._skills.get(job_id, []))
            return job

    def update_job(self, job: Job) -> Job:
        with self._lock:
            self._jobs[job.id] = job
            job.skills = list(self._skills.get(job.id, []))
            return job

    def delete_job(self, job_id: int) -> bool:
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                self._skills.pop(job_id, None)
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
        with self._lock:
            results = []
            for j in self._jobs.values():
                if employer_id is not None and j.employer_id != employer_id:
                    continue
                if is_active is not None and j.is_active != is_active:
                    continue
                if search:
                    q = search.lower()
                    if (
                        q not in j.title.lower()
                        and q not in j.company_name.lower()
                        and q not in j.description.lower()
                    ):
                        continue
                j.skills = list(self._skills.get(j.id, []))
                results.append(j)
            total = len(results)
            return results[skip : skip + limit], total

    def upsert_skill(
        self,
        job_id_or_skill: Any,
        skill_id_or_skill: Any = None,
        required_level: Optional[int] = None,
        mandatory: bool = True,
    ) -> JobSkill:
        with self._lock:
            if isinstance(job_id_or_skill, JobSkill):
                req = job_id_or_skill
                job_id = req.job_id
            elif isinstance(skill_id_or_skill, JobSkill):
                req = skill_id_or_skill
                job_id = job_id_or_skill
            else:
                job_id = job_id_or_skill
                req = JobSkill(
                    id=0,
                    job_id=job_id,
                    skill_id=skill_id_or_skill,
                    required_level=required_level or 1,
                    mandatory=mandatory,
                )

            reqs = self._skills.setdefault(job_id, [])
            for r in reqs:
                if r.skill_id == req.skill_id:
                    r.required_level = req.required_level
                    r.mandatory = req.mandatory
                    return r

            req.id = self._next_req_id
            self._next_req_id += 1
            req.created_at = datetime.now(timezone.utc)
            reqs.append(req)
            return req

    def delete_skill(self, job_id: int, skill_id: int) -> bool:
        with self._lock:
            reqs = self._skills.get(job_id, [])
            initial_len = len(reqs)
            self._skills[job_id] = [r for r in reqs if r.skill_id != skill_id]
            return len(self._skills[job_id]) < initial_len

    def get_skills(self, job_id: int) -> List[JobSkill]:
        with self._lock:
            return list(self._skills.get(job_id, []))

    # Compatibility aliases
    upsert_requirement = upsert_skill
    delete_requirement = delete_skill
    get_requirements = get_skills


class InMemoryMatchingRepository(MatchingRepositoryProtocol):
    def __init__(self):
        self._lock = threading.RLock()
        self._analysis_runs: Dict[str, AnalysisRun] = {}
        self._recommendations: Dict[str, List[Recommendation]] = {}
        self._next_rec_id = 1

    def save_analysis(
        self, run: AnalysisRun, items: List[AnalysisItem], recs: List[Recommendation]
    ) -> AnalysisRun:
        with self._lock:
            self._analysis_runs[run.id] = run
            run.items = items
            rec_list = []
            for rec in recs:
                rec.id = self._next_rec_id
                self._next_rec_id += 1
                rec_list.append(rec)
            self._recommendations[run.id] = rec_list
            run.recommendations = rec_list
            return run

    save_analysis_run = save_analysis

    def get_analysis_run(self, run_id: str) -> Optional[AnalysisRun]:
        with self._lock:
            run = self._analysis_runs.get(run_id)
            if run:
                run.recommendations = list(self._recommendations.get(run_id, []))
            return run

    def list_runs_for_student(
        self, student_id: int, skip: int = 0, limit: int = 50
    ) -> Tuple[List[AnalysisRun], int]:
        with self._lock:
            runs = [r for r in self._analysis_runs.values() if r.student_id == student_id]
            runs.sort(key=lambda r: r.created_at, reverse=True)
            for r in runs:
                r.recommendations = list(self._recommendations.get(r.id, []))
            total = len(runs)
            return runs[skip : skip + limit], total

    def get_latest_run(self, student_id: int, job_id: int) -> Optional[AnalysisRun]:
        with self._lock:
            runs = [
                r for r in self._analysis_runs.values()
                if r.student_id == student_id and r.job_id == job_id
            ]
            if not runs:
                return None
            runs.sort(key=lambda r: r.created_at, reverse=True)
            latest = runs[0]
            latest.recommendations = list(self._recommendations.get(latest.id, []))
            return latest

    def list_recommendations(self, student_id: int, job_id: int) -> List[Recommendation]:
        with self._lock:
            latest = self.get_latest_run(student_id, job_id)
            if latest:
                return list(self._recommendations.get(latest.id, []))
            return []

    def list_candidate_runs_for_job(
        self, job_id: int, skip: int = 0, limit: int = 50
    ) -> Tuple[List[AnalysisRun], int]:
        with self._lock:
            student_latest: Dict[int, AnalysisRun] = {}
            runs = [r for r in self._analysis_runs.values() if r.job_id == job_id]
            runs.sort(key=lambda r: r.created_at)
            for r in runs:
                student_latest[r.student_id] = r

            candidate_list = list(student_latest.values())
            candidate_list.sort(
                key=lambda r: (r.overall_match_percentage, r.created_at), reverse=True
            )
            for r in candidate_list:
                r.recommendations = list(self._recommendations.get(r.id, []))
            total = len(candidate_list)
            return candidate_list[skip : skip + limit], total

    def get_recommendations_for_run(self, run_id: str) -> List[Recommendation]:
        with self._lock:
            return list(self._recommendations.get(run_id, []))


class InMemoryApplicationRepository(ApplicationRepositoryProtocol):
    def __init__(self):
        self._lock = threading.RLock()
        self._applications: Dict[int, Application] = {}
        self._next_id = 1

    def create_application(self, app: Application) -> Application:
        with self._lock:
            app.id = self._next_id
            self._next_id += 1
            now = datetime.now(timezone.utc)
            app.created_at = now
            app.updated_at = now
            self._applications[app.id] = app
            return app

    def get_application_by_id(self, app_id: int) -> Optional[Application]:
        with self._lock:
            return self._applications.get(app_id)

    def get_active_application(self, student_id: int, job_id: int) -> Optional[Application]:
        with self._lock:
            for app in self._applications.values():
                if (
                    app.student_id == student_id
                    and app.job_id == job_id
                    and app.status not in (ApplicationStatus.WITHDRAWN, ApplicationStatus.CLOSED)
                ):
                    return app
            return None

    def update_application(self, app: Application) -> Application:
        with self._lock:
            app.updated_at = datetime.now(timezone.utc)
            self._applications[app.id] = app
            return app

    def list_applications(
        self,
        student_id: Optional[int] = None,
        job_id: Optional[int] = None,
        status: Optional[ApplicationStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Application], int]:
        with self._lock:
            results = list(self._applications.values())
            if student_id is not None:
                results = [a for a in results if a.student_id == student_id]
            if job_id is not None:
                results = [a for a in results if a.job_id == job_id]
            if status is not None:
                results = [a for a in results if a.status == status]
            results.sort(key=lambda a: a.created_at, reverse=True)
            total = len(results)
            return results[skip : skip + limit], total


# Singleton container for in-memory repositories
class RepositoryContainer:
    def __init__(self, db: Optional[Any] = None):
        if db is not None:
            from app.repositories.mysql_repo import (
                MySQLApplicationRepository,
                MySQLJobRepository,
                MySQLMatchingRepository,
                MySQLSkillRepository,
                MySQLStudentRepository,
                MySQLUserRepository,
            )
            self.user_repo = MySQLUserRepository(db)
            self.skill_repo = MySQLSkillRepository(db)
            self.student_repo = MySQLStudentRepository(db)
            self.job_repo = MySQLJobRepository(db)
            self.matching_repo = MySQLMatchingRepository(db)
            self.application_repo = MySQLApplicationRepository(db)
        else:
            self.user_repo = InMemoryUserRepository()
            self.skill_repo = InMemorySkillRepository()
            self.student_repo = InMemoryStudentRepository()
            self.job_repo = InMemoryJobRepository()
            self.matching_repo = InMemoryMatchingRepository()
            self.application_repo = InMemoryApplicationRepository()


default_repositories = RepositoryContainer()
