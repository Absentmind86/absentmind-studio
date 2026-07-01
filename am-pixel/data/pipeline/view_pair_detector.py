"""
View-pair candidate detection within sprite sheets (CHANGE-017).

Heuristics (candidates only — human confirmation happens in pair_annotator):
- identical canonical palette (same character, different direction), and
- identical or near-identical bounding-box dimensions, and
- silhouette IoU between A and mirrored-B above threshold (walk-cycle
  side views mirror), or IoU between A and B above threshold (front/back).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import IndexedSprite  # noqa: E402


@dataclass
class PairCandidate:
    sprite_a: str
    sprite_b: str
    kind: str  # "mirror" | "same-facing"
    silhouette_iou: float


def _silhouette(s: IndexedSprite) -> np.ndarray:
    return s.grid != 0


def _iou(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        return 0.0
    inter = np.count_nonzero(a & b)
    union = np.count_nonzero(a | b)
    return inter / union if union else 0.0


def detect_pairs(
    sprites: dict[str, IndexedSprite],
    *,
    iou_threshold: float = 0.72,
) -> list[PairCandidate]:
    out: list[PairCandidate] = []
    items = sorted(sprites.items())
    for i, (id_a, a) in enumerate(items):
        sil_a = _silhouette(a)
        for id_b, b in items[i + 1 :]:
            if a.palette != b.palette or a.grid.shape != b.grid.shape:
                continue
            sil_b = _silhouette(b)
            same = _iou(sil_a, sil_b)
            mirror = _iou(sil_a, sil_b[:, ::-1])
            best, kind = max((same, "same-facing"), (mirror, "mirror"))
            if best >= iou_threshold and same < 0.995:  # 0.995+: duplicate frame, not a view pair
                out.append(PairCandidate(id_a, id_b, kind, round(float(best), 4)))
    return out
