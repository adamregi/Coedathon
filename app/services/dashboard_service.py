from collections import Counter, defaultdict
from typing import Any, Dict, List
from app.core.errors import PermissionDeniedException
from app.domain.models import ApplicationStatus, Role, User
from app.domain.protocols import (
    ApplicationRepositoryProtocol,
    JobRepositoryProtocol,
    MatchingRepositoryProtocol,
    SkillRepositoryProtocol,
    StudentRepositoryProtocol,
    UserRepositoryProtocol,
)
from app.schemas.dashboard import (
    AdminDashboardRead,
    EmployerDashboardRead,
    SkillGapMetric,
    StudentDashboardRead,
)


class DashboardService:
    def __init__(
        self,
        user_repo: UserRepositoryProtocol,
        skill_repo: SkillRepositoryProtocol,
        student_repo: StudentRepositoryProtocol,
        job_repo: JobRepositoryProtocol,
        matching_repo: MatchingRepositoryProtocol,
        application_repo: ApplicationRepositoryProtocol,
    ):
        self.user_repo = user_repo
        self.skill_repo = skill_repo
        self.student_repo = student_repo
        self.job_repo = job_repo
        self.matching_repo = matching_repo
        self.application_repo = application_repo

    def get_student_dashboard(self, student_user: User) -> StudentDashboardRead:
        if student_user.role != Role.STUDENT:
            raise PermissionDeniedException("Only students can access student dashboard metrics")

        apps, total_apps = self.application_repo.list_applications(
            student_id=student_user.id, limit=1000
        )
        active_apps = [
            a for a in apps
            if a.status not in (ApplicationStatus.WITHDRAWN, ApplicationStatus.CLOSED, ApplicationStatus.REJECTED)
        ]

        runs, _ = self.matching_repo.list_runs_for_student(student_user.id, limit=100)
        avg_match = (
            sum(r.overall_match_percentage for r in runs) / len(runs)
            if runs
            else 0.0
        )

        # Aggregate skill gaps from recommendations
        skill_gap_counts: Dict[int, List[int]] = defaultdict(list)
        for r in runs:
            for rec in r.recommendations:
                skill_gap_counts[rec.skill_id].append(rec.gap)

        top_gaps: List[SkillGapMetric] = []
        for skill_id, gaps in skill_gap_counts.items():
            skill = self.skill_repo.get_by_id(skill_id)
            if skill:
                top_gaps.append(
                    SkillGapMetric(
                        skill_name=skill.name,
                        category=skill.category,
                        count=len(gaps),
                        avg_gap=round(sum(gaps) / len(gaps), 2),
                    )
                )
        top_gaps.sort(key=lambda g: (g.count, g.avg_gap), reverse=True)

        recent_analyses = [
            {
                "analysis_run_id": r.id,
                "job_id": r.job_id,
                "overall_match_percentage": r.overall_match_percentage,
                "calculated_at": r.created_at.isoformat(),
            }
            for r in runs[:5]
        ]

        return StudentDashboardRead(
            total_applications=total_apps,
            active_applications=len(active_apps),
            average_match_percentage=round(avg_match, 2),
            top_skill_gaps=top_gaps[:5],
            recent_analyses=recent_analyses,
        )

    def get_employer_dashboard(self, employer_user: User) -> EmployerDashboardRead:
        if employer_user.role not in (Role.EMPLOYER, Role.ADMIN):
            raise PermissionDeniedException("Only employers or admins can access employer dashboard metrics")

        jobs, total_jobs = self.job_repo.list_jobs(employer_id=employer_user.id, limit=1000)
        active_jobs = [j for j in jobs if j.is_active]
        job_ids = {j.id for j in jobs}

        all_candidate_runs = []
        for j in jobs:
            runs, _ = self.matching_repo.list_candidate_runs_for_job(j.id, limit=100)
            all_candidate_runs.extend(runs)

        avg_candidate_match = (
            sum(r.overall_match_percentage for r in all_candidate_runs) / len(all_candidate_runs)
            if all_candidate_runs
            else 0.0
        )

        # Gaps across employer's candidates
        skill_gap_counts: Dict[int, List[int]] = defaultdict(list)
        for r in all_candidate_runs:
            for rec in r.recommendations:
                skill_gap_counts[rec.skill_id].append(rec.gap)

        top_gaps: List[SkillGapMetric] = []
        for skill_id, gaps in skill_gap_counts.items():
            skill = self.skill_repo.get_by_id(skill_id)
            if skill:
                top_gaps.append(
                    SkillGapMetric(
                        skill_name=skill.name,
                        category=skill.category,
                        count=len(gaps),
                        avg_gap=round(sum(gaps) / len(gaps), 2),
                    )
                )
        top_gaps.sort(key=lambda g: (g.count, g.avg_gap), reverse=True)

        all_apps, _ = self.application_repo.list_applications(limit=1000)
        employer_apps = [a for a in all_apps if a.job_id in job_ids]

        recent_applications = [
            {
                "application_id": a.id,
                "student_id": a.student_id,
                "job_id": a.job_id,
                "status": a.status.value,
                "match_percentage_snapshot": a.match_percentage_snapshot,
                "applied_at": a.created_at.isoformat(),
            }
            for a in employer_apps[:5]
        ]

        return EmployerDashboardRead(
            total_jobs=total_jobs,
            active_jobs=len(active_jobs),
            total_candidates=len(all_candidate_runs),
            average_candidate_match=round(avg_candidate_match, 2),
            top_skill_gaps=top_gaps[:5],
            recent_applications=recent_applications,
        )

    def get_admin_dashboard(self, admin_user: User) -> AdminDashboardRead:
        if admin_user.role != Role.ADMIN:
            raise PermissionDeniedException("Only admins can access platform dashboard metrics")

        users, total_users = self.user_repo.list_all(limit=10000)
        students = [u for u in users if u.role == Role.STUDENT]
        employers = [u for u in users if u.role == Role.EMPLOYER]

        jobs, _ = self.job_repo.list_jobs(is_active=True, limit=10000)
        apps, total_apps = self.application_repo.list_applications(limit=10000)

        # Global average match percentage from all applications
        avg_match = (
            sum(a.match_percentage_snapshot for a in apps) / len(apps)
            if apps
            else 0.0
        )

        # Most demanded skills in job requirements
        all_jobs, _ = self.job_repo.list_jobs(limit=10000)
        skill_counts: Counter[int] = Counter()
        for j in all_jobs:
            for req in j.requirements:
                skill_counts[req.skill_id] += 1

        top_demanded = []
        for skill_id, count in skill_counts.most_common(5):
            skill = self.skill_repo.get_by_id(skill_id)
            if skill:
                top_demanded.append(
                    {
                        "skill_id": skill.id,
                        "skill_name": skill.name,
                        "category": skill.category,
                        "demand_count": count,
                    }
                )

        return AdminDashboardRead(
            total_users=total_users,
            total_students=len(students),
            total_employers=len(employers),
            total_active_jobs=len(jobs),
            total_applications=total_apps,
            platform_average_match=round(avg_match, 2),
            top_demanded_skills=top_demanded,
        )

    def get_live_dashboard(self, actor: User) -> Dict[str, Any]:
        """Calculates live platform aggregates from actual MySQL database records.
        Does not return hardcoded values.
        """
        _, total_students = self.student_repo.list_students(limit=1)
        _, total_jobs = self.job_repo.list_jobs(is_active=True, limit=1)
        apps, total_apps = self.application_repo.list_applications(limit=1000)

        avg_match = (
            round(sum(a.match_percentage_snapshot for a in apps) / len(apps), 1)
            if apps
            else 0.0
        )

        all_jobs, _ = self.job_repo.list_jobs(limit=100)
        gap_counter: Counter[int] = Counter()
        for j in all_jobs:
            for s in j.skills:
                gap_counter[s.skill_id] += 1

        top_gaps = []
        for skill_id, count in gap_counter.most_common(5):
            skill = self.skill_repo.get_by_id(skill_id)
            if skill:
                top_gaps.append({
                    "skill_id": skill.id,
                    "skill_name": skill.name,
                    "category": skill.category,
                    "gap_count": count,
                })

        return {
            "total_students": total_students,
            "total_jobs": total_jobs,
            "total_applications": total_apps,
            "average_skill_match": avg_match,
            "top_skill_gaps": top_gaps,
        }
