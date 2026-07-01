"""
Tile seam validation (SPEC §5.3, Rubric B Seam Integrity).

A tile is self-seamless when, tiled in a 2x2 grid, the color-change rate
across the wrap seams is no harsher than the tile's internal change rate.
Pairs of different tiles are validated the same way across their shared edge.
Deterministic and calibrated against wrapped-noise tiles (seamless by
construction) vs random crops (not seamless).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import load_rgba  # noqa: E402

EDGES = ("top", "bottom", "left", "right")


@dataclass
class SeamReport:
    ok: bool
    seam_ratio: float  # seam change rate / internal change rate (1.0 = invisible seam)
    failed_edges: list[str]

    def summary(self) -> str:
        state = "seamless" if self.ok else f"SEAM VISIBLE on {', '.join(self.failed_edges)}"
        return f"{state} (seam/internal change ratio {self.seam_ratio:.2f})"


def _row_change(a: np.ndarray, b: np.ndarray) -> float:
    """Mean absolute RGB change between two pixel rows/columns."""
    return float(np.abs(a[:, :3].astype(int) - b[:, :3].astype(int)).mean())


def _internal_change(tile: np.ndarray) -> float:
    h = tile.shape[0]
    changes = [_row_change(tile[y], tile[y + 1]) for y in range(h - 1)]
    v = tile.transpose(1, 0, 2)
    changes += [_row_change(v[x], v[x + 1]) for x in range(v.shape[0] - 1)]
    return max(float(np.mean(changes)), 1e-6)


def check_self(tile: np.ndarray, *, max_ratio: float = 1.8) -> SeamReport:
    """Validate that a tile tiles seamlessly with itself on all four edges."""
    internal = _internal_change(tile)
    seams = {
        "top": _row_change(tile[0], tile[-1]),  # bottom row wraps to top row
        "bottom": _row_change(tile[-1], tile[0]),
        "left": _row_change(tile.transpose(1, 0, 2)[0], tile.transpose(1, 0, 2)[-1]),
        "right": _row_change(tile.transpose(1, 0, 2)[-1], tile.transpose(1, 0, 2)[0]),
    }
    failed = [e for e, s in seams.items() if s / internal > max_ratio]
    ratio = max(seams.values()) / internal
    return SeamReport(ok=not failed, seam_ratio=round(ratio, 3), failed_edges=failed)


def check_pair(tile_a: np.ndarray, tile_b: np.ndarray, edge: str, *, max_ratio: float = 1.8) -> SeamReport:
    """Validate the seam when tile_b sits at `edge` of tile_a ('right' = B to the right of A)."""
    if edge not in EDGES:
        raise ValueError(f"edge must be one of {EDGES}")
    internal = max(_internal_change(tile_a), _internal_change(tile_b))
    if edge == "right":
        seam = _row_change(tile_a.transpose(1, 0, 2)[-1], tile_b.transpose(1, 0, 2)[0])
    elif edge == "left":
        seam = _row_change(tile_b.transpose(1, 0, 2)[-1], tile_a.transpose(1, 0, 2)[0])
    elif edge == "bottom":
        seam = _row_change(tile_a[-1], tile_b[0])
    else:
        seam = _row_change(tile_b[-1], tile_a[0])
    ratio = seam / internal
    return SeamReport(ok=ratio <= max_ratio, seam_ratio=round(ratio, 3), failed_edges=[] if ratio <= max_ratio else [edge])


def boundary_conditioning_tokens(left_neighbor: np.ndarray | None, upper_neighbor: np.ndarray | None) -> dict:
    """CHANGE-012 sliding-window boundary conditioning: ground-truth edge rows
    prepended to tile generation. Returns raw pixel rows; the tokenizer maps
    them to palette indices under the tileset's palette."""
    out: dict = {}
    if left_neighbor is not None:
        out["left_column"] = left_neighbor[:, -1].copy()
    if upper_neighbor is not None:
        out["top_row"] = upper_neighbor[-1, :].copy()
    return out


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("tile")
    args = p.parse_args()
    print(check_self(load_rgba(args.tile)).summary())


if __name__ == "__main__":
    main()
