"""
Icon set visual-grammar validation (SPEC §5.4).

Within a category (weapons, consumables, status icons...), icons must share:
identical canvas size, similar outline weight (outline-pixel share), and a
harmonized palette (pairwise palette overlap). Flags the outliers.
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
from tools.outline_checker import _outline_pixels  # noqa: E402


@dataclass
class IconSetReport:
    ok: bool
    outliers: dict[str, list[str]] = field(default_factory=dict)  # icon name -> problems


def check_set(icons: dict[str, np.ndarray]) -> IconSetReport:
    report = IconSetReport(ok=True)
    if len(icons) < 2:
        return report

    sizes = {name: a.shape[:2] for name, a in icons.items()}
    from collections import Counter

    common_size = Counter(sizes.values()).most_common(1)[0][0]

    weights = {}
    for name, a in icons.items():
        vis = int(np.count_nonzero(alpha_mask(a))) or 1
        weights[name] = len(_outline_pixels(a)) / vis
    median_w = float(np.median(list(weights.values())))

    palettes = {name: set(unique_colors(a)) for name, a in icons.items()}
    union: set = set().union(*palettes.values())

    for name in icons:
        problems = []
        if sizes[name] != common_size:
            problems.append(f"size {sizes[name][1]}x{sizes[name][0]} differs from set size {common_size[1]}x{common_size[0]}")
        if median_w and abs(weights[name] - median_w) / median_w > 0.5:
            problems.append(f"outline weight {weights[name]:.2f} far from set median {median_w:.2f}")
        others = union - palettes[name]
        overlap = len(palettes[name] & (union - palettes[name] if others else palettes[name]))
        if len(palettes[name]) and overlap / len(palettes[name]) < 0.2 and len(icons) > 2:
            problems.append("palette shares <20% with the rest of the set")
        if problems:
            report.outliers[name] = problems
            report.ok = False
    return report


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("icons", nargs="+")
    args = p.parse_args()
    report = check_set({Path(i).stem: load_rgba(i) for i in args.icons})
    if report.ok:
        print("icon set grammar OK")
    else:
        for name, probs in report.outliers.items():
            print(f"{name}: {'; '.join(probs)}")


if __name__ == "__main__":
    main()
