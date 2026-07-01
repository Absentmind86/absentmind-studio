"""
Pixel classification for structure-aware token ordering (CHANGE-001/CHANGE-014).

Four categories (foundation training default — reliable from geometry alone):
  0 TRANSPARENT      alpha = 0
  1 OUTLINE          visible pixel 4-adjacent to transparency or canvas border
  2 STRUCTURAL       large contiguous same-index region (>= structural_min area)
  3 NON_STRUCTURAL   everything else (shade + detail combined)

Five categories (--full-five-category, Stage 2 Golden Dataset only — CHANGE-014):
  NON_STRUCTURAL splits into
  3 SHADE            pixel's color shares a hue ramp with an adjacent STRUCTURAL
                     region's color (it reads as that region's shadow/highlight)
  4 DETAIL           everything else
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import (  # noqa: E402
    IndexedSprite,
    TRANSPARENT_INDEX,
    cluster_ramps,
    connected_region_sizes,
    outline_mask,
)

TRANSPARENT, OUTLINE, STRUCTURAL, NON_STRUCTURAL = 0, 1, 2, 3
SHADE, DETAIL = 3, 4  # five-category mode reuses 3 for SHADE and adds 4

CATEGORY_NAMES_4 = ("transparent", "outline", "structural", "non_structural")
CATEGORY_NAMES_5 = ("transparent", "outline", "structural", "shade", "detail")


def classify(
    sprite: IndexedSprite,
    *,
    structural_min: int | None = None,
    full_five_category: bool = False,
) -> np.ndarray:
    """(H, W) int8 category grid."""
    grid = sprite.grid
    h, w = grid.shape
    if structural_min is None:
        # scale with sprite area; a 16x24 sprite -> regions of 8+ px are structural
        structural_min = max(6, (h * w) // 48)

    cat = np.full((h, w), NON_STRUCTURAL, dtype=np.int8)
    cat[grid == TRANSPARENT_INDEX] = TRANSPARENT

    out = outline_mask(grid)
    cat[out] = OUTLINE

    sizes = connected_region_sizes(grid)
    structural = (sizes >= structural_min) & (grid != TRANSPARENT_INDEX) & ~out
    cat[structural] = STRUCTURAL

    if full_five_category:
        cat = _split_shade_detail(sprite, cat)
    return cat


def _split_shade_detail(sprite: IndexedSprite, cat: np.ndarray) -> np.ndarray:
    ramps = cluster_ramps(sprite.palette)
    ramp_of: dict[int, int] = {}
    flat = 1
    for ri, ramp in enumerate(ramps):
        for _ in ramp:
            ramp_of[flat] = ri
            flat += 1

    grid = sprite.grid
    h, w = grid.shape
    out = cat.copy()
    ys, xs = np.nonzero(cat == NON_STRUCTURAL)
    for y, x in zip(ys, xs):
        my_ramp = ramp_of.get(int(grid[y, x]))
        is_shade = False
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and cat[ny, nx] == STRUCTURAL:
                if ramp_of.get(int(grid[ny, nx])) == my_ramp:
                    is_shade = True
                    break
        out[y, x] = SHADE if is_shade else DETAIL
    return out


def category_distribution(cat: np.ndarray, *, five: bool = False) -> dict[str, float]:
    names = CATEGORY_NAMES_5 if five else CATEGORY_NAMES_4
    total = cat.size
    return {name: float(np.count_nonzero(cat == i)) / total for i, name in enumerate(names)}


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Classify pixels of an indexed sprite (.npz)")
    p.add_argument("npz")
    p.add_argument("--full-five-category", action="store_true")
    args = p.parse_args()
    sprite = IndexedSprite.load_npz(args.npz)
    cat = classify(sprite, full_five_category=args.full_five_category)
    for name, frac in category_distribution(cat, five=args.full_five_category).items():
        print(f"{name:16s} {frac:6.2%}")


if __name__ == "__main__":
    main()
