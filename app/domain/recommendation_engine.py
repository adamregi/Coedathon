"""Pure domain recommendation engine.

Contains pure Python rules for generating prioritized learning recommendations.
Has zero dependencies on FastAPI, Pydantic, SQLAlchemy, or database sessions.
"""

from typing import Any, Dict, List, Optional


class PriorityStr(str):
    """String subclass that compares equal case-insensitively while preserving uppercase display."""
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.upper() == other.upper()
        return super().__eq__(other)

    def __hash__(self) -> int:
        return hash(self.upper())


def determine_recommendation_reason(mandatory: bool) -> str:
    """Determine recommendation reason based on requirement type.

    Rules:
    - Mandatory gap: 'Mandatory job requirement'
    - Optional gap: 'Required supporting skill'
    - Fallback: 'Required proficiency gap'
    """
    if mandatory is True:
        return "Mandatory job requirement"
    elif mandatory is False:
        return "Required supporting skill"
    return "Required proficiency gap"


def determine_recommendation_priority(mandatory: bool, gap: int) -> PriorityStr:
    """Determine recommendation priority based on requirement type and gap magnitude.

    Rules:
    - Mandatory gap >= 2: HIGH
    - Mandatory gap = 1: MEDIUM
    - Optional gap >= 2: MEDIUM
    - Optional gap = 1: LOW
    """
    if mandatory:
        return PriorityStr("HIGH") if gap >= 2 else PriorityStr("MEDIUM")
    else:
        return PriorityStr("MEDIUM") if gap >= 2 else PriorityStr("LOW")


def generate_recommendations(
    analysis_run_id: str,
    student_id: int,
    job_id: int,
    analysis_items: List[Dict[str, Any]],
    skill_names: Optional[Dict[int, str]] = None,
) -> List[Dict[str, Any]]:
    """Generate prioritized recommendations for unmet skill requirements.

    Rules:
    - gap = 0 -> NO recommendation generated
    - Sort:
      1. Mandatory first (True before False)
      2. Gap descending
      3. Skill name ascending
    """
    skill_names = skill_names or {}
    recommendations: List[Dict[str, Any]] = []

    for item in analysis_items:
        gap = item.get("gap", 0)
        if gap <= 0:
            continue

        skill_id = item["skill_id"]
        required_level = item["required_level"]
        current_level = item.get("current_level", 0)
        mandatory = bool(item.get("mandatory", True))
        skill_name = skill_names.get(skill_id, f"Skill #{skill_id}")

        reason = determine_recommendation_reason(mandatory)
        priority = determine_recommendation_priority(mandatory, gap)

        recommendations.append({
            "analysis_run_id": analysis_run_id,
            "student_id": student_id,
            "job_id": job_id,
            "skill_id": skill_id,
            "skill_name": skill_name,
            "current_level": current_level,
            "target_level": required_level,
            "gap": gap,
            "mandatory": mandatory,
            "priority": priority,
            "reason": reason,
        })

    # Sort: 1. Mandatory first (not mandatory is False, so False < True -> mandatory=True comes first)
    # 2. Gap descending (-gap)
    # 3. Skill name ascending (skill_name.lower())
    recommendations.sort(
        key=lambda r: (
            0 if r["mandatory"] else 1,
            -r["gap"],
            r["skill_name"].lower(),
        )
    )

    return recommendations
