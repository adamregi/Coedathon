"""Pure domain matching engine.

Contains pure Python calculations for skill gaps and overall job match percentages.
Has zero dependencies on FastAPI, Pydantic, SQLAlchemy, or database sessions.
"""

from typing import Any, Dict, List, Tuple


def calculate_skill_gap(required_level: int, current_level: int) -> Dict[str, Any]:
    """Calculate proficiency gap and match status for a single skill.

    Rules:
    - gap = max(required_level - current_level, 0)
    - If current_level >= required_level -> MATCHED, gap = 0
    - If current_level < required_level -> GAP, gap > 0
    - Missing student skill -> current_level = 0
    """
    curr = max(current_level, 0)
    req = max(required_level, 1)

    gap = max(req - curr, 0)
    matched = curr >= req

    return {
        "required_level": req,
        "current_level": curr,
        "gap": gap,
        "matched": matched,
        "status": "MATCHED" if matched else "GAP",
    }


def calculate_overall_match(
    requirements: List[Dict[str, Any]],
    student_skills: Dict[int, int],
) -> Tuple[int, List[Dict[str, Any]]]:
    """Calculate overall weighted match percentage and individual skill gap breakdowns.

    Formula:
    - ratio = min(current / required, 1.0)
    - mandatory weight = 2.0
    - optional weight = 1.0
    - overall_match = round(100 * sum(weight * ratio) / sum(weight))
    - Empty requirements -> 100% match
    - Algorithm version: "v1.0"
    """
    if not requirements:
        return 100, []

    item_results: List[Dict[str, Any]] = []
    total_weighted_ratio = 0.0
    total_weight = 0.0

    for req in requirements:
        skill_id = req["skill_id"]
        required_level = req["required_level"]
        mandatory = bool(req.get("mandatory", True))

        current_level = student_skills.get(skill_id, 0)
        gap_info = calculate_skill_gap(required_level, current_level)

        weight = 2.0 if mandatory else 1.0
        ratio = min(current_level / float(required_level), 1.0) if required_level > 0 else 1.0

        total_weighted_ratio += weight * ratio
        total_weight += weight

        item_results.append({
            "skill_id": skill_id,
            "required_level": required_level,
            "current_level": current_level,
            "gap": gap_info["gap"],
            "matched": gap_info["matched"],
            "status": gap_info["status"],
            "mandatory": mandatory,
            "weight": weight,
            "ratio": ratio,
        })

    if total_weight > 0.0:
        overall_match = int(round(100.0 * (total_weighted_ratio / total_weight)))
    else:
        overall_match = 100

    return overall_match, item_results
