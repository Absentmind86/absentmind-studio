"""
Palette compliance validation (Rubric A/B/C Technical Compliance input).

Checks, with per-pixel coordinates for every violation:
- every color is in the allowed palette (DNA palette or MASTER_PALETTE ramps)
- color count within SNES limits (15 + transparent)
- all colors inside the SNES 15-bit color space
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import (  # noqa: E402
    MAX_SPRITE_COLORS,
    alpha_mask,
    is_snes_legal_color,
    load_rgba,
    unique_colors,
)


@dataclass
class PaletteReport:
    ok: bool
    n_colors: int
    out_of_palette: list[tuple[int, int, tuple[int, int, int]]] = field(default_factory=list)  # (x, y, rgb)
    non_snes_colors: list[tuple[int, int, int]] = field(default_factory=list)
    over_color_limit: bool = False

    def summary(self) -> str:
        if self.ok:
            return f"palette OK ({self.n_colors} colors)"
        parts = []
        if self.out_of_palette:
            first = self.out_of_palette[0]
            parts.append(f"{len(self.out_of_palette)} out-of-palette pixels (first at x={first[0]}, y={first[1]}, rgb={first[2]})")
        if self.non_snes_colors:
            parts.append(f"{len(self.non_snes_colors)} colors outside SNES 15-bit space")
        if self.over_color_limit:
            parts.append(f"{self.n_colors} colors exceeds limit {MAX_SPRITE_COLORS}")
        return "; ".join(parts)


def validate(
    rgba: np.ndarray,
    allowed_palette: list[tuple[int, int, int]] | None = None,
    *,
    max_colors: int = MAX_SPRITE_COLORS,
    enforce_snes_space: bool = True,
) -> PaletteReport:
    colors = unique_colors(rgba)
    report = PaletteReport(ok=True, n_colors=len(colors))

    if len(colors) > max_colors:
        report.over_color_limit = True
        report.ok = False

    if enforce_snes_space:
        report.non_snes_colors = [c for c in colors if not is_snes_legal_color(c)]
        if report.non_snes_colors:
            report.ok = False

    if allowed_palette is not None:
        allowed = set(allowed_palette)
        vis = alpha_mask(rgba)
        for y, x in zip(*np.nonzero(vis)):
            rgb = tuple(int(v) for v in rgba[y, x, :3])
            if rgb not in allowed:
                report.out_of_palette.append((int(x), int(y), rgb))
        if report.out_of_palette:
            report.ok = False
    return report


def score_technical_compliance(rgba: np.ndarray, allowed_palette: list | None, max_points: int) -> tuple[int, str]:
    """Rubric category scorer: full points iff zero violations (85/85 gate has no tolerance)."""
    r = validate(rgba, allowed_palette)
    return (max_points if r.ok else 0, r.summary())


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("sprite")
    args = p.parse_args()
    print(validate(load_rgba(args.sprite)).summary())


if __name__ == "__main__":
    main()
