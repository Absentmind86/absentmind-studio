"""
Battle effect timing/weight evaluation (SPEC §5.6, Rubric A effects variant).

Deterministic checks on the effect manifest + frames:
- frame count within the category's convention range
- timing shape: anticipation -> impact -> dissipation (impact frames are the
  shortest; dissipation decays) — evaluated from per-frame tick durations
- energy curve: visible-pixel mass should peak mid-sequence, not first frame
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import alpha_mask  # noqa: E402

FRAME_RANGES = {
    "projectile": (3, 10),
    "area": (5, 16),
    "status": (3, 12),
    "healing": (4, 12),
    "elemental": (4, 12),
    "summon": (10, 40),
    "hit_impact": (2, 6),
    "death": (4, 16),
    "environmental": (3, 12),
}


@dataclass
class EffectReport:
    ok: bool
    problems: list[str] = field(default_factory=list)
    energy_curve: list[float] = field(default_factory=list)


def evaluate(
    frames: list[np.ndarray],
    *,
    category: str,
    tick_durations: list[int] | None = None,
) -> EffectReport:
    report = EffectReport(ok=True)
    lo, hi = FRAME_RANGES.get(category, (2, 40))
    if not (lo <= len(frames) <= hi):
        report.ok = False
        report.problems.append(f"{len(frames)} frames outside {category} convention {lo}..{hi}")

    energy = [float(np.count_nonzero(alpha_mask(f))) for f in frames]
    total = max(energy) or 1.0
    report.energy_curve = [round(e / total, 3) for e in energy]
    if len(frames) >= 4:
        peak = int(np.argmax(energy))
        if peak == 0:
            report.ok = False
            report.problems.append("energy peaks on frame 0 — no anticipation/build-up")
        if energy[-1] > 0.85 * total:
            report.ok = False
            report.problems.append("final frame keeps near-peak energy — no dissipation")

    if tick_durations is not None:
        if len(tick_durations) != len(frames):
            report.ok = False
            report.problems.append("tick_durations length does not match frame count")
        elif len(frames) >= 4:
            peak = int(np.argmax(energy))
            if tick_durations[peak] > min(tick_durations):
                report.problems.append(
                    "impact frame is not the fastest — consider shortening peak frames for weight"
                )
    return report


def score_animation_quality(frames: list[np.ndarray], category: str, max_points: int) -> tuple[int, str]:
    r = evaluate(frames, category=category)
    return (max_points if r.ok else 0, "; ".join(r.problems) or "timing/weight conventions met")
