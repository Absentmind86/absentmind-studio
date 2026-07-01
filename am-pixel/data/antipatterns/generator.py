"""
Anti-pattern dataset generator (SPEC §8.5, ROADMAP Phase 3).

Takes known-good procedural sprites (validation_corpus synthesis) and applies
labeled corruptions that reproduce the classic pixel-art failure modes:

- pillow_shading : concentric shading rings around the region centroid,
                   ignoring the light source
- banding        : shading replaced with straight parallel bands hugging
                   the outline (staircase banding)
- black_outline  : outline set to pure #000000 (must be darkened local color)
- anti_aliasing  : blend colors inserted along color boundaries (sub-pixel
                   smoothing — illegal in SNES style)

Each output is a (bad, corrected, label) triple in data/antipatterns/labeled/.
Used to calibrate the evaluation engine — Phase 5 gate requires 90%+ detection.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from data.pipeline.validation_corpus import make_character  # noqa: E402
from tools._common import alpha_mask, save_rgba, snes_quantize_channel  # noqa: E402

LABELED_DIR = _AM_PIXEL / "data" / "antipatterns" / "labeled"


def corrupt_pillow_shading(arr: np.ndarray) -> np.ndarray:
    out = arr.copy()
    vis = alpha_mask(out)
    ys, xs = np.nonzero(vis)
    if len(ys) == 0:
        return out
    colors = out[vis][:, :3]
    uniq = np.unique(colors.reshape(-1, 3), axis=0)
    by_v = sorted((tuple(int(v) for v in c) for c in uniq), key=sum)
    if len(by_v) < 3:
        return out
    dark, mid, light = by_v[0], by_v[len(by_v) // 2], by_v[-1]
    cy, cx = ys.mean(), xs.mean()
    d = np.sqrt((ys - cy) ** 2 + (xs - cx) ** 2)
    lo, hi = np.percentile(d, 33), np.percentile(d, 72)
    for y, x, dist in zip(ys, xs, d):
        out[y, x, :3] = light if dist <= lo else (mid if dist <= hi else dark)
    return out


def corrupt_banding(arr: np.ndarray) -> np.ndarray:
    out = arr.copy()
    vis = alpha_mask(out)
    colors = out[vis][:, :3]
    uniq = np.unique(colors.reshape(-1, 3), axis=0)
    by_v = sorted((tuple(int(v) for v in c) for c in uniq), key=sum)
    if len(by_v) < 3:
        return out
    h, w = vis.shape
    for y in range(h):
        for x in range(w):
            if vis[y, x]:
                out[y, x, :3] = by_v[(y // 2) % 3]  # parallel horizontal bands
    return out


def corrupt_black_outline(arr: np.ndarray) -> np.ndarray:
    out = arr.copy()
    vis = alpha_mask(out)
    h, w = vis.shape
    for y in range(h):
        for x in range(w):
            if not vis[y, x]:
                continue
            if (
                y in (0, h - 1) or x in (0, w - 1)
                or not vis[y - 1, x] or not vis[y + 1, x]
                or not vis[y, x - 1] or not vis[y, x + 1]
            ):
                out[y, x, :3] = (0, 0, 0)
    return out


def corrupt_anti_aliasing(arr: np.ndarray) -> np.ndarray:
    out = arr.copy()
    vis = alpha_mask(out)
    h, w = vis.shape
    src = arr.copy()
    for y in range(h):
        for x in range(w - 1):
            if not (vis[y, x] and vis[y, x + 1]):
                continue
            a, b = src[y, x, :3].astype(int), src[y, x + 1, :3].astype(int)
            if np.abs(a - b).sum() > 96 and (y + x) % 2 == 0:
                blend = tuple(snes_quantize_channel(int(v)) for v in ((a + b) // 2))
                out[y, x, :3] = blend  # sub-pixel smoothing artifact
    return out


CORRUPTIONS = {
    "pillow_shading": corrupt_pillow_shading,
    "banding": corrupt_banding,
    "black_outline": corrupt_black_outline,
    "anti_aliasing": corrupt_anti_aliasing,
}


def build_antipattern_dataset(n_per_type: int = 130, seed: int = 99, out_dir: Path | None = None) -> int:
    """Generate n_per_type labeled (bad, corrected) pairs per corruption type."""
    rng = np.random.default_rng(seed)
    out = Path(out_dir or LABELED_DIR)
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    for name, fn in CORRUPTIONS.items():
        for i in range(n_per_type):
            good = make_character(rng, width=16, height=int(rng.choice([16, 24])))
            bad = fn(good)
            if np.array_equal(good, bad):
                continue  # corruption was a no-op on this sprite; skip
            stem = f"{name}_{i:04d}"
            save_rgba(bad, out / f"{stem}_bad.png")
            save_rgba(good, out / f"{stem}_corrected.png")
            (out / f"{stem}_label.json").write_text(
                json.dumps(
                    {
                        "failure_mode": name,
                        "bad": f"{stem}_bad.png",
                        "corrected": f"{stem}_corrected.png",
                        "rubric_category": {
                            "pillow_shading": "construction_quality",
                            "banding": "construction_quality",
                            "black_outline": "construction_quality",
                            "anti_aliasing": "technical_compliance",
                        }[name],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            count += 1
    return count


def main() -> None:
    n = build_antipattern_dataset()
    print(f"anti-pattern dataset: {n} labeled pairs in {LABELED_DIR}")


if __name__ == "__main__":
    main()
