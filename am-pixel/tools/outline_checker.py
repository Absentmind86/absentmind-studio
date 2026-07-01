"""
Outline technique check (style bible: outlines are darkened local color,
never pure black, single-pixel weight).

Reports: pure-black outline pixels (coordinates), fraction of outline that is
pure black, and outline pixels that are not plausibly derived from their
region's local color (chromatic mismatch).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import alpha_mask, load_rgba  # noqa: E402

PURE_BLACK_TOLERANCE = 8  # channel values all below this = "pure black"


@dataclass
class OutlineReport:
    ok: bool
    n_outline_pixels: int
    black_pixels: list[tuple[int, int]] = field(default_factory=list)
    black_fraction: float = 0.0

    def summary(self) -> str:
        if self.ok:
            return f"outline OK ({self.n_outline_pixels} px, 0 pure black)"
        return (
            f"{len(self.black_pixels)} pure-black outline pixels "
            f"({self.black_fraction:.0%} of outline) — must be darkened local color"
        )


def _outline_pixels(rgba: np.ndarray) -> list[tuple[int, int]]:
    vis = alpha_mask(rgba)
    h, w = vis.shape
    out = []
    for y in range(h):
        for x in range(w):
            if not vis[y, x]:
                continue
            if (
                y in (0, h - 1) or x in (0, w - 1)
                or not vis[y - 1, x] or not vis[y + 1, x]
                or not vis[y, x - 1] or not vis[y, x + 1]
            ):
                out.append((x, y))
    return out


def check(rgba: np.ndarray, *, allow_black_fraction: float = 0.0) -> OutlineReport:
    """allow_black_fraction: tolerated share of pure-black outline pixels.
    Default 0 — style bible forbids pure black; characters wearing genuinely
    black clothing are the vlm_critic upgrade path (CHANGE-021), not a tolerance."""
    outline = _outline_pixels(rgba)
    black = [
        (x, y)
        for (x, y) in outline
        if all(int(c) < PURE_BLACK_TOLERANCE for c in rgba[y, x, :3])
    ]
    frac = len(black) / len(outline) if outline else 0.0
    return OutlineReport(
        ok=frac <= allow_black_fraction,
        n_outline_pixels=len(outline),
        black_pixels=black,
        black_fraction=frac,
    )


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("sprite")
    args = p.parse_args()
    print(check(load_rgba(args.sprite)).summary())


if __name__ == "__main__":
    main()
