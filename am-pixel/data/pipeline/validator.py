"""
Corpus-entry validation: SNES palette compliance + provenance gate.

A sprite may enter the training corpus only if:
1. it has a provenance manifest entry (Constitution Rule 5 — checked here,
   at the last write barrier, in addition to scraper-side checks), and
2. it passes SNES compliance (color count, 15-bit color space), and
3. it is within sane pixel-art dimensions.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from data.pipeline import provenance  # noqa: E402
from tools._common import (  # noqa: E402
    MAX_SPRITE_COLORS,
    is_snes_legal_color,
    unique_colors,
)

MAX_DIMENSION = 128  # corpus sprites; multi-tile bosses are segmented upstream
MIN_DIMENSION = 8


@dataclass
class ValidationResult:
    ok: bool
    problems: list[str] = field(default_factory=list)


def validate_rgba(rgba: np.ndarray) -> ValidationResult:
    problems = []
    h, w = rgba.shape[:2]
    if not (MIN_DIMENSION <= h <= MAX_DIMENSION and MIN_DIMENSION <= w <= MAX_DIMENSION):
        problems.append(f"dimensions {w}x{h} outside {MIN_DIMENSION}..{MAX_DIMENSION}")
    colors = unique_colors(rgba)
    if not colors:
        problems.append("sprite is fully transparent")
    if len(colors) > MAX_SPRITE_COLORS:
        problems.append(f"{len(colors)} colors exceeds SNES max {MAX_SPRITE_COLORS}")
    illegal = [c for c in colors if not is_snes_legal_color(c)]
    if illegal:
        problems.append(f"{len(illegal)} colors outside SNES 15-bit space (quantize first)")
    return ValidationResult(ok=not problems, problems=problems)


def validate_corpus_entry(
    sprite_id: str,
    rgba: np.ndarray,
    manifest_path: Path | None = None,
) -> ValidationResult:
    result = validate_rgba(rgba)
    if not provenance.has(sprite_id, manifest_path):
        result.problems.append(
            f"no provenance manifest entry for {sprite_id!r} — refusing corpus write "
            "(Constitution Rule 5)"
        )
        result.ok = False
    return result
