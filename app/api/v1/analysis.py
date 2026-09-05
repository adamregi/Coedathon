from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import (
    get_current_user,
    get_matching_service,
    get_student_service,
    require_employer_or_admin,
    require_student,
)
from app.domain.models import User
from app.schemas.envelope import ResponseEnvelope, success_envelope
from app.schemas.matching import (
    AnalysisRunRead,
    CandidateRankingItemRead,
)
from app.schemas.student import StudentProfileRead
from app.services.matching_service import MatchingService
from app.services.student_service import StudentService

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/jobs/{job_id}", response_model=ResponseEnvelope[AnalysisRunRead], status_code=status.HTTP_201_CREATED)
def trigger_student_match_analysis(
    job_id: int,
    student_user: User = Depends(require_student),
    matching_service: MatchingService = Depends(get_matching_service),
):
    """
    Student triggers an immutable match/gap analysis against a specific job posting.
    Calculates weighted score (mandatory=2, optional=1) using Matching Engine v1.0.
    """
    analysis = matching_service.calculate_and_save_analysis(
        student_user_id=student_user.id,
        job_id=job_id,
        actor=student_user,
    )
    return success_envelope(data=analysis.model_dump())


@router.get("/history/me", response_model=ResponseEnvelope[List[AnalysisRunRead]])
def list_my_analyses(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    student_user: User = Depends(require_student),
    matching_service: MatchingService = Depends(get_matching_service),
):
    """Retrieve historical immutable analysis runs for the logged-in student."""
    skip = (page - 1) * per_page
    runs, total = matching_service.list_student_runs(
        student_id=student_user.id, actor=student_user, skip=skip, limit=per_page
    )
    return success_envelope(
        data=[r.model_dump() for r in runs],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/{run_id}", response_model=ResponseEnvelope[AnalysisRunRead])
def get_analysis_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    matching_service: MatchingService = Depends(get_matching_service),
):
    """Fetch an immutable analysis run by UUID, including snapshot and skill gap breakdown."""
    run = matching_service.get_analysis_run(run_id, actor=current_user)
    return success_envelope(data=run.model_dump())


@router.get("/jobs/{job_id}/candidates", response_model=ResponseEnvelope[List[CandidateRankingItemRead]])
def get_candidate_rankings_for_job(
    job_id: int,
    skill: Optional[str] = Query(None, description="Filter candidates by specific skill name"),
    min_proficiency: Optional[int] = Query(None, ge=1, le=5, description="Filter by minimum skill proficiency"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_employer_or_admin),
    matching_service: MatchingService = Depends(get_matching_service),
):
    """
    Employer / Admin: Retrieve candidate ranking for an employer-owned job,
    sorted match-descending, with optional skill-based filtering.
    """
    skip = (page - 1) * per_page
    candidates, total = matching_service.list_candidate_rankings_for_job(
        job_id=job_id,
        actor=current_user,
        skill_name=skill,
        min_proficiency=min_proficiency,
        skip=skip,
        limit=per_page,
    )
    return success_envelope(
        data=[c.model_dump() for c in candidates],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/jobs/{job_id}/candidates/{student_id}/profile", response_model=ResponseEnvelope[StudentProfileRead])
def access_candidate_profile(
    job_id: int,
    student_id: int,
    current_user: User = Depends(require_employer_or_admin),
    matching_service: MatchingService = Depends(get_matching_service),
    student_service: StudentService = Depends(get_student_service),
):
    """
    Gated Access: Employers can inspect the full student profile exclusively
    for candidates who have matching records on their owned job.
    """
    # Gated check in matching_service
    profile = matching_service.access_candidate_student_profile(
        student_id=student_id, job_id=job_id, employer=current_user
    )
    profile_read = student_service._to_profile_read(profile)
    return success_envelope(data=profile_read.model_dump())
