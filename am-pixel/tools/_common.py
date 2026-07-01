"""
Shared sprite/palette primitives used by tools/ and data/pipeline/.

The core data model everywhere in AM Pixel:

- RGBA sprite: numpy uint8 array of shape (H, W, 4).
- IndexedSprite: canonical palette + (H, W) int grid of palette indices.
  Index 0 is ALWAYS transparent. Remaining indices are canonically
  ramp-ordered per CHANGE-032: colors clustered into hue ramps, ramps
  ordered by mean hue, colors within a ramp ordered dark -> light.

SNES 15-bit color: 5 bits per channel. An 8-bit channel value is
SNES-legal when it is a multiple of 8 (c >> 3 << 3 round-trips).
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

TRANSPARENT_INDEX = 0
MAX_SPRITE_COLORS = 15  # + 1 transparent = 16 SNES palette slots


def load_rgba(path: Path | str) -> np.ndarray:
    """Load any image file as an (H, W, 4) uint8 RGBA array."""
    with Image.open(path) as im:
        return np.asarray(im.convert("RGBA"), dtype=np.uint8).copy()


def save_rgba(arr: np.ndarray, path: Path | str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr.astype(np.uint8), "RGBA").save(path)


def snes_quantize_channel(c: int) -> int:
    """Quantize an 8-bit channel to SNES 5-bit (expanded back to 8-bit)."""
    return (c >> 3) << 3


def is_snes_legal_color(rgb: tuple[int, int, int]) -> bool:
    return all(c == snes_quantize_channel(c) for c in rgb)


def snes_quantize_rgba(arr: np.ndarray) -> np.ndarray:
    """Quantize all color channels to the SNES 15-bit space; alpha binarized."""
    out = arr.copy()
    out[..., :3] = (out[..., :3] >> 3) << 3
    out[..., 3] = np.where(out[..., 3] >= 128, 255, 0)
    return out


def alpha_mask(arr: np.ndarray) -> np.ndarray:
    """(H, W) bool — True where the pixel is visible (alpha >= 128)."""
    return arr[..., 3] >= 128


def unique_colors(arr: np.ndarray) -> list[tuple[int, int, int]]:
    """Unique opaque RGB colors in an RGBA sprite."""
    vis = arr[alpha_mask(arr)][:, :3]
    if len(vis) == 0:
        return []
    return [tuple(int(v) for v in c) for c in np.unique(vis, axis=0)]


def _hue_sat_val(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    r, g, b = (c / 255.0 for c in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h, s, v


def _hue_distance(h1: float, h2: float) -> float:
    d = abs(h1 - h2)
    return min(d, 1.0 - d)


def cluster_ramps(
    colors: list[tuple[int, int, int]],
    hue_threshold: float = 0.09,
) -> list[list[tuple[int, int, int]]]:
    """
    Greedy hue clustering into ramps (CHANGE-032 mechanism 1).

    Near-grays (saturation < 0.12) form their own ramp: hue is meaningless
    for them, and grouping them by hue splits gray ramps arbitrarily.
    Within each ramp, colors are ordered dark -> light (by value, then
    saturation for stability). Ramps are ordered by mean hue, with the
    gray ramp always first (most sprites use it for outlines/neutrals).
    """
    grays: list[tuple[int, int, int]] = []
    chromatic: list[tuple[int, int, int]] = []
    for c in colors:
        (grays if _hue_sat_val(c)[1] < 0.12 else chromatic).append(c)

    ramps: list[list[tuple[int, int, int]]] = []
    for c in sorted(chromatic, key=lambda c: _hue_sat_val(c)[0]):
        h = _hue_sat_val(c)[0]
        for ramp in ramps:
            mean_h = float(np.mean([_hue_sat_val(x)[0] for x in ramp]))
            if _hue_distance(h, mean_h) <= hue_threshold:
                ramp.append(c)
                break
        else:
            ramps.append([c])

    def dark_to_light(ramp: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
        return sorted(ramp, key=lambda c: (_hue_sat_val(c)[2], -_hue_sat_val(c)[1]))

    ordered = [dark_to_light(r) for r in ramps]
    ordered.sort(key=lambda r: float(np.mean([_hue_sat_val(c)[0] for c in r])))
    if grays:
        ordered.insert(0, dark_to_light(grays))
    return ordered


def canonical_palette(colors: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    """Flatten ramp clusters into the canonical index order (index 0 = transparent
    is implicit and NOT included in the returned list — the list starts at index 1)."""
    return [c for ramp in cluster_ramps(colors) for c in ramp]


@dataclass
class IndexedSprite:
    """Canonical indexed sprite. palette[i] is the RGB for index i+1; index 0 = transparent."""

    palette: list[tuple[int, int, int]]
    grid: np.ndarray  # (H, W) int16, values 0..len(palette)
    meta: dict = field(default_factory=dict)

    @property
    def height(self) -> int:
        return int(self.grid.shape[0])

    @property
    def width(self) -> int:
        return int(self.grid.shape[1])

    def color_of(self, index: int) -> tuple[int, int, int] | None:
        if index == TRANSPARENT_INDEX:
            return None
        return self.palette[index - 1]

    def to_rgba(self) -> np.ndarray:
        h, w = self.grid.shape
        out = np.zeros((h, w, 4), dtype=np.uint8)
        for idx in range(1, len(self.palette) + 1):
            m = self.grid == idx
            out[m, :3] = self.palette[idx - 1]
            out[m, 3] = 255
        return out

    def save_npz(self, path: Path | str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            palette=np.asarray(self.palette, dtype=np.uint8),
            grid=self.grid.astype(np.int16),
            meta=np.frombuffer(_meta_bytes(self.meta), dtype=np.uint8),
        )

    @classmethod
    def load_npz(cls, path: Path | str) -> "IndexedSprite":
        data = np.load(path, allow_pickle=False)
        meta = _meta_from_bytes(data["meta"].tobytes()) if "meta" in data else {}
        palette = [tuple(int(v) for v in c) for c in data["palette"]]
        return cls(palette=palette, grid=data["grid"].astype(np.int16), meta=meta)


def _meta_bytes(meta: dict) -> bytes:
    import json

    return json.dumps(meta, sort_keys=True).encode("utf-8")


def _meta_from_bytes(b: bytes) -> dict:
    import json

    try:
        return json.loads(b.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return {}


def outline_mask(grid: np.ndarray) -> np.ndarray:
    """(H, W) bool — visible pixels 4-adjacent to transparency or the canvas border."""
    vis = grid != TRANSPARENT_INDEX
    padded = np.pad(vis, 1, constant_values=False)
    n = (
        padded[:-2, 1:-1]
        & padded[2:, 1:-1]
        & padded[1:-1, :-2]
        & padded[1:-1, 2:]
    )
    return vis & ~n


def connected_region_sizes(grid: np.ndarray) -> np.ndarray:
    """(H, W) int — for each visible pixel, the size of its same-index 4-connected region."""
    from collections import deque

    h, w = grid.shape
    sizes = np.zeros((h, w), dtype=np.int32)
    seen = np.zeros((h, w), dtype=bool)
    for y in range(h):
        for x in range(w):
            if seen[y, x] or grid[y, x] == TRANSPARENT_INDEX:
                continue
            idx = grid[y, x]
            q = deque([(y, x)])
            seen[y, x] = True
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and grid[ny, nx] == idx:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            for cy, cx in cells:
                sizes[cy, cx] = len(cells)
    return sizes
