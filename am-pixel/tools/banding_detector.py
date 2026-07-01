"""
Banding detection (classic pixel-art anti-pattern).

Banding = adjacent shading colors running in straight parallel bands of equal
thickness (usually hugging the outline or axis-aligned), instead of shaped
shading. Detector heuristic: measure the share of color-boundary segments
that are long straight runs aligned with the same boundary shifted by one
row/column. High parallel-run share = banding.

Calibrated against data/antipatterns (corrupt_banding vs clean sprites).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import alpha_mask, load_rgba  # noqa: E402

MIN_RUN = 4  # boundary runs shorter than this are ignored (normal dithering/steps)


@dataclass
class BandingReport:
    ok: bool
    parallel_run_share: float
    n_boundary_pixels: int

    def summary(self) -> str:
        state = "OK" if self.ok else "BANDING DETECTED"
        return f"{state} — parallel straight-run share {self.parallel_run_share:.0%} of {self.n_boundary_pixels} boundary px"


def _color_key(rgba: np.ndarray) -> np.ndarray:
    """(H, W) int key per pixel; -1 for transparent."""
    vis = alpha_mask(rgba)
    key = (
        rgba[..., 0].astype(np.int32) << 16
    ) | (rgba[..., 1].astype(np.int32) << 8) | rgba[..., 2].astype(np.int32)
    key[~vis] = -1
    return key


def _straight_run_pixels(key: np.ndarray) -> tuple[int, int]:
    """Count horizontal boundary pixels, and those inside straight parallel runs.

    A horizontal boundary at (y, x) exists when key[y,x] != key[y+1,x] (both visible).
    It belongs to a parallel run when >= MIN_RUN consecutive x share the same
    (upper color, lower color) pair — a straight band edge."""
    h, w = key.shape
    boundary = 0
    banded = 0
    for y in range(h - 1):
        x = 0
        while x < w:
            a, b = key[y, x], key[y + 1, x]
            if a == -1 or b == -1 or a == b:
                x += 1
                continue
            run = 1
            while x + run < w and key[y, x + run] == a and key[y + 1, x + run] == b:
                run += 1
            boundary += run
            if run >= MIN_RUN:
                banded += run
            x += run
    return boundary, banded


def check(rgba: np.ndarray, *, max_parallel_share: float = 0.55) -> BandingReport:
    key = _color_key(rgba)
    b1, band1 = _straight_run_pixels(key)
    b2, band2 = _straight_run_pixels(key.T)  # vertical boundaries
    boundary, banded = b1 + b2, band1 + band2
    share = banded / boundary if boundary else 0.0
    return BandingReport(ok=share <= max_parallel_share, parallel_run_share=share, n_boundary_pixels=boundary)


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("sprite")
    args = p.parse_args()
    print(check(load_rgba(args.sprite)).summary())


if __name__ == "__main__":
    main()
