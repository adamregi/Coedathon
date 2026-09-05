import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from app.core.audit import emit_audit_event
from app.core.errors import (
    PermissionDeniedException,
    ResourceNotFoundException,
)
from app.domain.matching_engine import calculate_overall_match
from app.domain.models import (
    AnalysisItem,
    AnalysisRun,
    Job,
    Recommendation,
    Role,
    StudentProfile,
    User,
)
from app.domain.protocols import (
    JobRepositoryProtocol,
    MatchingRepositoryProtocol,
    SkillRepositoryProtocol,
    StudentRepositoryProtocol,
    UserRepositoryProtocol,
)
from app.domain.recommendation_engine import generate_recommendations
from app.schemas.matching import (
    AnalysisRunRead,
    CandidateRankingItemRead,
    RecommendationRead,
    SkillMatchResultRead,
)


class MatchingService:
    ALGORITHM_VERSION = "v1.0"

    def __init__(
        self,
        matching_repo: MatchingRepositoryProtocol,
        job_repo: JobRepositoryProtocol,
        student_repo: StudentRepositoryProtocol,
        skill_repo: SkillRepositoryProtocol,
        user_repo: UserRepositoryProtocol,
    ):
        self.matching_repo = matching_repo
        self.job_repo = job_repo
        self.student_repo = student_repo
        self.skill_repo = skill_repo
        self.user_repo = user_repo

    def _resolve_student_profile(self, student_id_or_user_id: int) -> StudentProfile:
        # First try by student_id
        profile = self.student_repo.get_student_by_id(student_id_or_user_id)
        if profile:
            return profile
        # Then try by user_id
        profile = self.student_repo.get_student_by_user_id(student_id_or_user_id)
        if profile:
            return profile
        # If student user exists, auto-provision profile
        if self.user_repo:
            user = self.user_repo.get_by_id(student_id_or_user_id)
            if user and user.role == Role.STUDENT:
                try:
                    return self.student_repo.create_student(
                        StudentProfile(
                            student_id=0,
                            name=user.full_name,
                            email=user.email,
                            user_id=user.id,
                        )
                    )
                except Exception:
                    pass
        raise ResourceNotFoundException(f"Student profile with ID/User ID {student_id_or_user_id} not found")

    def calculate_and_save_analysis(
        self,
        student_id: Optional[int] = None,
        job_id: int = 0,
        actor: Optional[User] = None,
        student_user_id: Optional[int] = None,
        **kwargs,
    ) -> AnalysisRunRead:
        target_id = student_id if student_id is not None else student_user_id
        if target_id is None:
            raise ResourceNotFoundException("Student ID or User ID is required")
        profile = self._resolve_student_profile(target_id)

        # Cross-student privacy guard: Student A cannot run analysis for Student B
        if actor and actor.role == Role.STUDENT and actor.id != profile.user_id:
            raise PermissionDeniedException("Students can only run analyses for themselves")

        job = self.job_repo.get_job_by_id(job_id)
        if not job:
            raise ResourceNotFoundException(f"Job with ID {job_id} not found")

        # Student skills map: skill_id -> proficiency
        student_skills = {s.skill_id: s.proficiency for s in profile.skills}

        # Format requirements for pure domain matching engine
        req_dicts = []
        skill_names = {}
        for s in job.skills:
            skill = self.skill_repo.get_by_id(s.skill_id)
            name = skill.name if skill else f"Skill #{s.skill_id}"
            skill_names[s.skill_id] = name
            req_dicts.append({
                "skill_id": s.skill_id,
                "required_level": s.required_level,
                "mandatory": s.mandatory,
            })

        # Calculate using pure domain matching engine
        overall_match, item_results = calculate_overall_match(req_dicts, student_skills)

        run_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Generate recommendations using pure domain recommendation engine
        rec_dicts = generate_recommendations(
            analysis_run_id=run_id,
            student_id=profile.student_id,
            job_id=job.id,
            analysis_items=item_results,
            skill_names=skill_names,
        )

        analysis_items: List[AnalysisItem] = []
        for it in item_results:
            skill = self.skill_repo.get_by_id(it["skill_id"])
            analysis_items.append(
                AnalysisItem(
                    id=0,
                    analysis_run_id=run_id,
                    skill_id=it["skill_id"],
                    required_level=it["required_level"],
                    current_level=it["current_level"],
                    gap=it["gap"],
                    matched=it["matched"],
                    mandatory=it["mandatory"],
                    skill_name=skill.name if skill else None,
                    category=skill.category if skill else None,
                )
            )

        recommendations: List[Recommendation] = []
        for rd in rec_dicts:
            recommendations.append(
                Recommendation(
                    id=0,
                    student_id=profile.student_id,
                    job_id=job.id,
                    skill_id=rd["skill_id"],
                    current_level=rd["current_level"],
                    target_level=rd["target_level"],
                    analysis_run_id=run_id,
                    priority=rd["priority"],
                    reason=rd["reason"],
                    skill_name=rd["skill_name"],
                    created_at=now,
                )
            )

        run = AnalysisRun(
            id=run_id,
            student_id=profile.student_id,
            job_id=job.id,
            algorithm_version=self.ALGORITHM_VERSION,
            overall_match_percentage=overall_match,
            created_at=now,
            items=analysis_items,
            recommendations=recommendations,
        )

        saved_run = self.matching_repo.save_analysis(run, analysis_items, recommendations)

        emit_audit_event(
            action="ANALYSIS_RUN_CALCULATED",
            actor_id=actor.id,
            actor_role=actor.role.value,
            target_type="analysis_run",
            target_id=saved_run.id,
            details={
                "student_id": profile.student_id,
                "job_id": job.id,
                "overall_match": overall_match,
            },
        )

        return self._to_analysis_read(saved_run)

    def get_analysis_run(self, run_id: str, actor: User) -> AnalysisRunRead:
        run = self.matching_repo.get_analysis_run(run_id)
        if not run:
            raise ResourceNotFoundException(f"Analysis run '{run_id}' not found")

        # Students can only view their own runs
        if actor.role == Role.STUDENT:
            profile = self.student_repo.get_student_by_user_id(actor.id)
            if not profile or profile.student_id != run.student_id:
                raise PermissionDeniedException("Students can only view their own analysis runs")

        return self._to_analysis_read(run)

    def get_recommendations_for_student_job(
        self, student_id: int, job_id: int, actor: User
    ) -> List[RecommendationRead]:
        profile = self._resolve_student_profile(student_id)

        # Cross-student privacy guard: Student A cannot view recommendations for Student B
        if actor.role == Role.STUDENT and actor.id != profile.user_id:
            raise PermissionDeniedException("Students can only view their own recommendations")

        recs = self.matching_repo.list_recommendations(profile.student_id, job_id)
        if not recs:
            # If no existing analysis, run one first to generate recommendations
            analysis = self.calculate_and_save_analysis(profile.student_id, job_id, actor)
            return analysis.recommendations

        return [
            RecommendationRead(
                id=r.id,
                analysis_run_id=r.analysis_run_id,
                skill_id=r.skill_id,
                skill_name=r.skill_name or f"Skill #{r.skill_id}",
                suggested_action=r.suggested_action,
                priority=r.priority,
                gap=r.gap,
                reason=r.reason,
                resource_url=None,
                created_at=r.created_at,
            )
            for r in recs
        ]

    def list_student_runs(
        self, student_id: int, actor: User, skip: int = 0, limit: int = 50
    ) -> Tuple[List[AnalysisRunRead], int]:
        profile = self._resolve_student_profile(student_id)
        if actor.role == Role.STUDENT and actor.id != profile.user_id:
            raise PermissionDeniedException("Students can only view their own analysis history")

        runs, total = self.matching_repo.list_runs_for_student(profile.student_id, skip=skip, limit=limit)
        return [self._to_analysis_read(r) for r in runs], total

    def list_candidate_rankings_for_job(
        self, job_id: int, actor: User, skip: int = 0, limit: int = 50
    ) -> Tuple[List[CandidateRankingItemRead], int]:
        job = self.job_repo.get_job_by_id(job_id)
        if not job:
            raise ResourceNotFoundException(f"Job with ID {job_id} not found")

        runs, total = self.matching_repo.list_candidate_runs_for_job(job_id, skip=skip, limit=limit)
        candidates = []
        for r in runs:
            student = self.student_repo.get_student_by_id(r.student_id)
            candidates.append(
                CandidateRankingItemRead(
                    student_id=student.user_id if student and student.user_id else r.student_id,
                    student_name=student.name if student else "Unknown",
                    student_email=student.email if student else "",
                    overall_match_percentage=r.overall_match_percentage,
                    analysis_run_id=r.id,
                    calculated_at=r.created_at,
                )
            )
        return candidates, total

    def access_candidate_student_profile(
        self, student_id: int, job_id: int, employer: User
    ) -> StudentProfile:
        job = self.job_repo.get_job_by_id(job_id)
        if not job:
            raise ResourceNotFoundException(f"Job with ID {job_id} not found")

        if employer.role != Role.ADMIN and job.employer_id != employer.id:
            raise PermissionDeniedException("Access denied: You do not own this job posting")

        profile = self._resolve_student_profile(student_id)
        return profile

    def _to_analysis_read(self, run: AnalysisRun) -> AnalysisRunRead:
        item_reads = [
            SkillMatchResultRead(
                skill_id=i.skill_id,
                skill_name=i.skill_name or f"Skill #{i.skill_id}",
                category=i.category or "General",
                required_proficiency=i.required_level,
                current_proficiency=i.current_level,
                mandatory=i.mandatory,
                gap=i.gap,
                matched=i.matched,
            )
            for i in run.items
        ]
        rec_reads = [
            RecommendationRead(
                id=r.id,
                analysis_run_id=r.analysis_run_id,
                skill_id=r.skill_id,
                skill_name=r.skill_name or f"Skill #{r.skill_id}",
                suggested_action=r.suggested_action,
                priority=r.priority,
                gap=r.gap,
                reason=r.reason,
                resource_url=None,
                created_at=r.created_at,
            )
            for r in run.recommendations
        ]
        return AnalysisRunRead(
            id=run.id,
            student_id=run.student_id,
            job_id=run.job_id,
            algorithm_version=run.algorithm_version,
            overall_match_percentage=run.overall_match_percentage,
            skill_results=item_reads,
            recommendations=rec_reads,
            raw_snapshot=run.raw_snapshot,
            created_at=run.created_at,
        )
