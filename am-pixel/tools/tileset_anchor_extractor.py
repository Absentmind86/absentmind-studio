"""
Tileset Anchor extraction and conformance (SPEC §5.3, Rubric B Texture Coherence).

The Anchor is derived from the approved seed tiles: palette union, detail
density (color-boundary rate), and saturation/value feel. Every subsequent
tile is validated against it within tolerances.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import _hue_sat_val, load_rgba, unique_colors  # noqa: E402


@dataclass
class TilesetAnchor:
    palette: list[tuple[int, int, int]]
    detail_density: float  # boundary pixels / total pixels
    mean_saturation: float
    mean_value: float

    def to_json(self) -> str:
        return json.dumps(
            {
                "palette": [list(c) for c in self.palette],
                "detail_density": self.detail_density,
                "mean_saturation": self.mean_saturation,
                "mean_value": self.mean_value,
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, text: str) -> "TilesetAnchor":
        d = json.loads(text)
        return cls(
            palette=[tuple(c) for c in d["palette"]],
            detail_density=d["detail_density"],
            mean_saturation=d["mean_saturation"],
            mean_value=d["mean_value"],
        )


def _detail_density(tile: np.ndarray) -> float:
    rgb = tile[..., :3].astype(int)
    dh = np.abs(rgb[:, 1:] - rgb[:, :-1]).sum(axis=2) > 0
    dv = np.abs(rgb[1:, :] - rgb[:-1, :]).sum(axis=2) > 0
    return float((dh.sum() + dv.sum()) / tile[..., 0].size)


def _sat_val(colors: list[tuple[int, int, int]]) -> tuple[float, float]:
    if not colors:
        return 0.0, 0.0
    sv = [_hue_sat_val(c)[1:] for c in colors]
    return float(np.mean([s for s, _ in sv])), float(np.mean([v for _, v in sv]))


def extract_anchor(seed_tiles: list[np.ndarray]) -> TilesetAnchor:
    palette: set[tuple[int, int, int]] = set()
    densities = []
    for t in seed_tiles:
        palette.update(unique_colors(t))
        densities.append(_detail_density(t))
    sat, val = _sat_val(sorted(palette))
    return TilesetAnchor(
        palette=sorted(palette),
        detail_density=round(float(np.mean(densities)), 4),
        mean_saturation=round(sat, 4),
        mean_value=round(val, 4),
    )


def check_against_anchor(
    tile: np.ndarray,
    anchor: TilesetAnchor,
    *,
    density_tolerance: float = 0.5,  # relative
    sat_val_tolerance: float = 0.15,  # absolute
) -> tuple[bool, list[str]]:
    problems = []
    off = [c for c in unique_colors(tile) if c not in set(anchor.palette)]
    if off:
        problems.append(f"{len(off)} colors not in Tileset Anchor palette")
    d = _detail_density(tile)
    if anchor.detail_density and abs(d - anchor.detail_density) / anchor.detail_density > density_tolerance:
        problems.append(f"detail density {d:.3f} vs anchor {anchor.detail_density:.3f} (>{density_tolerance:.0%} off)")
    sat, val = _sat_val(unique_colors(tile))
    if abs(sat - anchor.mean_saturation) > sat_val_tolerance:
        problems.append(f"saturation feel {sat:.2f} vs anchor {anchor.mean_saturation:.2f}")
    if abs(val - anchor.mean_value) > sat_val_tolerance:
        problems.append(f"value feel {val:.2f} vs anchor {anchor.mean_value:.2f}")
    return (not problems, problems)


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("seed_tiles", nargs="+")
    p.add_argument("--out", default="tileset_anchor.json")
    args = p.parse_args()
    anchor = extract_anchor([load_rgba(t) for t in args.seed_tiles])
    Path(args.out).write_text(anchor.to_json() + "\n", encoding="utf-8")
    print(f"anchor written to {args.out}: {len(anchor.palette)} colors, density {anchor.detail_density}")


if __name__ == "__main__":
    main()
