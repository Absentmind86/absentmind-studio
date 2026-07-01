"""
Sprite extraction from sprite sheets.

Two modes:
- grid: fixed cell size (cols x rows known or inferred from cell dims)
- auto: alpha-connected-component bounding boxes (for irregular sheets)

Extracted sprites are trimmed to their bounding box and returned as RGBA arrays.
"""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import alpha_mask, load_rgba, save_rgba  # noqa: E402


def extract_grid(sheet: np.ndarray, cell_w: int, cell_h: int) -> list[np.ndarray]:
    """Slice a sheet into fixed-size cells, skipping fully transparent cells."""
    h, w = sheet.shape[:2]
    out = []
    for y0 in range(0, h - cell_h + 1, cell_h):
        for x0 in range(0, w - cell_w + 1, cell_w):
            cell = sheet[y0 : y0 + cell_h, x0 : x0 + cell_w]
            if alpha_mask(cell).any():
                out.append(cell.copy())
    return out


def extract_auto(sheet: np.ndarray, *, min_area: int = 16, gap: int = 1) -> list[np.ndarray]:
    """
    Connected-component extraction over the alpha mask (8-connectivity,
    bridging gaps up to `gap` px so anti-aliased fringes stay attached).
    Returns sprites trimmed to bounding boxes, raster order by top-left.
    """
    vis = alpha_mask(sheet)
    h, w = vis.shape
    seen = np.zeros_like(vis)
    boxes: list[tuple[int, int, int, int]] = []
    reach = gap + 1
    for y in range(h):
        for x in range(w):
            if not vis[y, x] or seen[y, x]:
                continue
            q = deque([(y, x)])
            seen[y, x] = True
            y0, y1, x0, x1, area = y, y, x, x, 0
            while q:
                cy, cx = q.popleft()
                area += 1
                y0, y1 = min(y0, cy), max(y1, cy)
                x0, x1 = min(x0, cx), max(x1, cx)
                for dy in range(-reach, reach + 1):
                    for dx in range(-reach, reach + 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and vis[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
            if area >= min_area:
                boxes.append((y0, x0, y1, x1))
    boxes.sort()
    return [sheet[y0 : y1 + 1, x0 : x1 + 1].copy() for (y0, x0, y1, x1) in boxes]


def extract_file(
    src: Path | str,
    out_dir: Path | str,
    *,
    cell: tuple[int, int] | None = None,
    prefix: str | None = None,
) -> list[Path]:
    sheet = load_rgba(src)
    sprites = extract_grid(sheet, *cell) if cell else extract_auto(sheet)
    out_dir = Path(out_dir)
    prefix = prefix or Path(src).stem
    paths = []
    for i, spr in enumerate(sprites):
        p = out_dir / f"{prefix}_{i:04d}.png"
        save_rgba(spr, p)
        paths.append(p)
    return paths


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Extract sprites from a sheet")
    p.add_argument("src")
    p.add_argument("out_dir")
    p.add_argument("--cell", help="WxH for fixed-grid extraction, e.g. 16x24")
    args = p.parse_args()
    cell = None
    if args.cell:
        w, h = args.cell.lower().split("x")
        cell = (int(w), int(h))
    paths = extract_file(args.src, args.out_dir, cell=cell)
    print(f"extracted {len(paths)} sprites to {args.out_dir}")


if __name__ == "__main__":
    main()
