"""
Structure-aware sequence reordering (CHANGE-001) with canvas coordinates
preserved (CHANGE-010). Output tokens are (palette_index, canvas_x, canvas_y)
tuples — plus the category, which the tokenizer uses for segment context.

Order: transparent -> outline -> structural -> non_structural
(five-category mode: ... -> shade -> detail). Within a category: raster order.
The ordering is deterministic and invertible given the sprite dimensions.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from data.pipeline.pixel_classifier import classify  # noqa: E402
from tools._common import IndexedSprite  # noqa: E402


@dataclass
class TokenSequence:
    """Parallel arrays, one entry per pixel, in structure-aware order."""

    indices: np.ndarray  # palette index per token (int16)
    xs: np.ndarray  # canvas x per token (int16)
    ys: np.ndarray  # canvas y per token (int16)
    categories: np.ndarray  # classifier category per token (int8)
    width: int
    height: int

    def __len__(self) -> int:
        return int(self.indices.shape[0])


def reorder(sprite: IndexedSprite, *, full_five_category: bool = False) -> TokenSequence:
    cat = classify(sprite, full_five_category=full_five_category)
    h, w = sprite.grid.shape
    order_i, order_x, order_y, order_c = [], [], [], []
    n_cats = int(cat.max()) + 1
    for c in range(n_cats):
        ys, xs = np.nonzero(cat == c)  # np.nonzero yields raster order (row-major)
        for y, x in zip(ys, xs):
            order_i.append(int(sprite.grid[y, x]))
            order_x.append(int(x))
            order_y.append(int(y))
            order_c.append(int(c))
    return TokenSequence(
        indices=np.asarray(order_i, dtype=np.int16),
        xs=np.asarray(order_x, dtype=np.int16),
        ys=np.asarray(order_y, dtype=np.int16),
        categories=np.asarray(order_c, dtype=np.int8),
        width=w,
        height=h,
    )


def reconstruct(seq: TokenSequence) -> np.ndarray:
    """Rebuild the (H, W) index grid from a token sequence — exact inverse of reorder."""
    grid = np.zeros((seq.height, seq.width), dtype=np.int16)
    grid[seq.ys, seq.xs] = seq.indices
    return grid
