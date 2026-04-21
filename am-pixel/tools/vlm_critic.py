"""VLM critic stub — semantic rubric fallback (CHANGE-021)."""
from typing import Any


def evaluate_borderline(
    sprite_path: str,
    criterion: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return JSON shape: criterion, pass, violations[], confidence. Not implemented in Phase 0."""
    raise NotImplementedError("vlm_critic — implement in Phase 5 if heuristic false-positive rate > 10%")
