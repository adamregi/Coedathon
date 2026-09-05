from typing import List
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, get_matching_service
from app.domain.models import User
from app.schemas.envelope import ResponseEnvelope, success_envelope
from app.schemas.matching import RecommendationRead
from app.services.matching_service import MatchingService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/analysis/{run_id}", response_model=ResponseEnvelope[List[RecommendationRead]])
def get_recommendations_for_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    matching_service: MatchingService = Depends(get_matching_service),
):
    """
    Retrieve prioritized recommendations for an immutable analysis run.
    Mandatory skill gaps are prioritized ahead of optional gaps, then ordered descending by gap size.
    """
    run = matching_service.get_analysis_run(run_id, actor=current_user)
    return success_envelope(data=[r.model_dump() for r in run.recommendations])
