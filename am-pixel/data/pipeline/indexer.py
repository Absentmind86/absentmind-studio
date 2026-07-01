"""
RGB -> canonical palette-index conversion (CHANGE-032 mechanism 1).

Indices are NOT arbitrary: index 0 = transparent; remaining colors are
clustered into hue ramps, ramps ordered by mean hue (gray ramp first),
colors within a ramp ordered dark -> light. Index positions therefore
carry stable relative semantics across the whole corpus — low ramp
positions are shadows, high are highlights — which is what makes
palette-index token prediction learnable across sprites with unrelated
palettes. See SPEC §3.1 Palette grounding.
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
    MAX_SPRITE_COLORS,
    TRANSPARENT_INDEX,
    alpha_mask,
    canonical_palette,
    load_rgba,
    snes_quantize_rgba,
    unique_colors,
)


def index_sprite(
    rgba: np.ndarray,
    *,
    quantize_snes: bool = True,
    max_colors: int = MAX_SPRITE_COLORS,
    meta: dict | None = None,
) -> IndexedSprite:
    """
    Convert an RGBA sprite to a canonical IndexedSprite.

    Raises ValueError if the sprite has more than `max_colors` opaque colors
    after SNES quantization — such sprites must be palette-reduced upstream
    (extractor/validator), not silently mangled here.
    """
    arr = snes_quantize_rgba(rgba) if quantize_snes else rgba.copy()
    colors = unique_colors(arr)
    if len(colors) > max_colors:
        raise ValueError(
            f"sprite has {len(colors)} colors after quantization; max is {max_colors} "
            "(palette-reduce upstream before indexing)"
        )
    palette = canonical_palette(colors)
    lookup = {c: i + 1 for i, c in enumerate(palette)}

    h, w = arr.shape[:2]
    grid = np.full((h, w), TRANSPARENT_INDEX, dtype=np.int16)
    vis = alpha_mask(arr)
    for y, x in zip(*np.nonzero(vis)):
        grid[y, x] = lookup[tuple(int(v) for v in arr[y, x, :3])]
    return IndexedSprite(palette=palette, grid=grid, meta=meta or {})


def index_file(src: Path | str, dst: Path | str, meta: dict | None = None) -> IndexedSprite:
    sprite = index_sprite(load_rgba(src), meta=meta)
    sprite.save_npz(dst)
    return sprite


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Index a sprite PNG to canonical .npz")
    p.add_argument("src")
    p.add_argument("dst")
    args = p.parse_args()
    s = index_file(args.src, args.dst)
    print(f"indexed {args.src}: {s.width}x{s.height}, {len(s.palette)} colors -> {args.dst}")


if __name__ == "__main__":
    main()
