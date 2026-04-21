"""
Rubric A/B/C — automated 85pt gate + human 15pt path (CHANGE-013).
Scores of 70+ automated points MUST include per-category evidence (CHANGE-028 Mechanism 2).
"""

from __future__ import annotations

from typing import Any, TypedDict


class CategoryEvidence(TypedDict, total=False):
    score: int
    tool: str
    tools: list[str]
    evidence: str


class AutomatedScoreResult(TypedDict, total=False):
    automated_score: int
    evidence_complete: bool
    categories: dict[str, CategoryEvidence]
    rejected: bool
    rejection_reason: str


def score_automated_with_evidence(
    asset_type: str,
    sprite_meta: dict[str, Any],
    category_results: dict[str, CategoryEvidence],
) -> AutomatedScoreResult:
    """
    When automated_score >= 70, every category contributing to the score must include
    tool name(s) and a plain-language evidence string. Incomplete evidence sets rejected=True.
    """
    total = sum(c.get("score", 0) for c in category_results.values())
    evidence_complete = all(
        bool(c.get("evidence")) and (bool(c.get("tool")) or bool(c.get("tools")))
        for c in category_results.values()
    )
    out: AutomatedScoreResult = {
        "automated_score": total,
        "evidence_complete": evidence_complete and total >= 70,
        "categories": category_results,
    }
    if total >= 70 and not evidence_complete:
        out["rejected"] = True
        out["rejection_reason"] = "Score >= 70 requires structured evidence per category (CHANGE-028)."
    return out


def main() -> None:
    raise NotImplementedError("Full rubric scoring — wire palette_validator, detectors, etc.")


if __name__ == "__main__":
    main()
