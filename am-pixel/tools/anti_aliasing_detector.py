"""
Anti-aliasing (sub-pixel blending) detection — not allowed in SNES style.

AA artifact signature: a rarely-used color that sits chromatically between two
adjacent colors and appears only along the boundary between those colors.
Flags each such pixel with coordinates.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import alpha_mask, load_rgba, unique_colors  # noqa: E402

RARE_FRACTION = 0.04  # a color used in <4% of visible pixels is "rare"
BLEND_TOLERANCE = 24  # max channel distance from the neighbor midpoint


@dataclass
class AAReport:
    ok: bool
    blend_pixels: list[tuple[int, int]] = field(default_factory=list)

    def summary(self) -> str:
        if self.ok:
            return "no sub-pixel blending detected"
        first = self.blend_pixels[0]
        return f"{len(self.blend_pixels)} anti-aliasing blend pixels (first at x={first[0]}, y={first[1]})"


def check(rgba: np.ndarray, *, max_blend_pixels: int = 0) -> AAReport:
    vis = alpha_mask(rgba)
    total_vis = int(np.count_nonzero(vis))
    if total_vis == 0:
        return AAReport(ok=True)
    colors = unique_colors(rgba)
    counts = {}
    flat = rgba[vis][:, :3]
    for c in colors:
        counts[c] = int(np.count_nonzero(np.all(flat == c, axis=1)))
    rare = {c for c, n in counts.items() if n / total_vis < RARE_FRACTION}

    h, w = vis.shape
    blends: list[tuple[int, int]] = []
    for y in range(h):
        for x in range(w):
            if not vis[y, x]:
                continue
            rgb = tuple(int(v) for v in rgba[y, x, :3])
            if rgb not in rare:
                continue
            # legitimate ramp mid-colors cluster (shading bands are contiguous);
            # true AA pixels are isolated — require no same-color 4-neighbor
            has_same_neighbor = any(
                0 <= ny < h and 0 <= nx < w and vis[ny, nx]
                and tuple(int(v) for v in rgba[ny, nx, :3]) == rgb
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
            )
            if has_same_neighbor:
                continue
            # gather distinct opposing neighbor pairs (horizontal and vertical)
            for (ay, ax), (by, bx) in (((y, x - 1), (y, x + 1)), ((y - 1, x), (y + 1, x))):
                if not (0 <= ax < w and 0 <= bx < w and 0 <= ay < h and 0 <= by < h):
                    continue
                if not (vis[ay, ax] and vis[by, bx]):
                    continue
                a = rgba[ay, ax, :3].astype(int)
                b = rgba[by, bx, :3].astype(int)
                if tuple(a) == rgb or tuple(b) == rgb or tuple(a) == tuple(b):
                    continue
                mid = (a + b) / 2
                if np.abs(np.asarray(rgb) - mid).max() <= BLEND_TOLERANCE:
                    blends.append((x, y))
                    break
    return AAReport(ok=len(blends) <= max_blend_pixels, blend_pixels=blends)


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("sprite")
    args = p.parse_args()
    print(check(load_rgba(args.sprite)).summary())


if __name__ == "__main__":
    main()
