"""
Tier 0 validation corpus builder (CHANGE-037).

Procedurally generates pixel-art-plausible sprites for smoke-testing the
pipeline, training loop, and evaluation stack end to end. Sprites follow the
style bible's structural rules so the whole toolchain exercises realistically:

- symmetric character silhouettes (head/torso/legs), 2-3 hue ramps
- hue-shifted 3-step ramps in SNES 15-bit space, dark -> light
- top-left light source: highlights up-left, shadows down-right per region
- outlines are darkened local color, never pure black
- seamlessly tiling texture tiles for tileset-path testing

Every sprite gets a provenance entry (tier 0, license "synthetic-validation")
written BEFORE the sprite file, same as the real scraper. Tier 0 never enters
production training (provenance.production_entries excludes it).

THIS IS NOT TRAINING DATA in the OPENCLAW_PROMPT sense. It exists so the
machinery is proven before real Tier 1/2 data arrives.
"""

from __future__ import annotations

import colorsys
import datetime as _dt
import sys
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from data.pipeline import provenance  # noqa: E402
from tools._common import save_rgba, snes_quantize_channel  # noqa: E402

DEFAULT_DIR = _AM_PIXEL / "data" / "validation_corpus"


def _snes(rgb: tuple[float, float, float]) -> tuple[int, int, int]:
    return tuple(snes_quantize_channel(int(max(0, min(255, round(c * 255))))) for c in rgb)


def make_ramp(rng: np.random.Generator, hue: float | None = None) -> list[tuple[int, int, int]]:
    """3-step hue-shifted ramp, dark -> light. Shadows shift toward blue/purple,
    highlights toward yellow — the hue-shift rule from MASTER_PALETTE."""
    h = float(rng.uniform(0, 1)) if hue is None else hue
    s = float(rng.uniform(0.45, 0.8))
    v = float(rng.uniform(0.55, 0.75))
    shadow = colorsys.hsv_to_rgb((h - 0.06) % 1.0, min(1.0, s + 0.15), max(0.15, v - 0.28))
    base = colorsys.hsv_to_rgb(h, s, v)
    light = colorsys.hsv_to_rgb((h + 0.05) % 1.0, max(0.15, s - 0.18), min(0.98, v + 0.22))
    ramp = [_snes(shadow), _snes(base), _snes(light)]
    # quantization can collapse steps on dark ramps — nudge until distinct
    while len(set(ramp)) < 3:
        v = min(0.9, v + 0.07)
        base = colorsys.hsv_to_rgb(h, s, v)
        light = colorsys.hsv_to_rgb((h + 0.05) % 1.0, max(0.15, s - 0.18), min(0.98, v + 0.25))
        ramp = [ramp[0], _snes(base), _snes(light)]
    return ramp


def _outline_color(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    """Darkened local color — never pure black (style bible outline rule)."""
    out = tuple(max(16, snes_quantize_channel(int(c * 0.45))) for c in rgb)
    return out if out != (0, 0, 0) else (16, 16, 24)


def _shade_region(canvas: np.ndarray, mask: np.ndarray, ramp: list[tuple[int, int, int]]) -> None:
    """Fill mask with ramp base; highlight the top-left band, shadow the
    bottom-right band (top-left light source)."""
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return
    d = (xs - xs.min()) + (ys - ys.min())  # distance along the light axis
    lo, hi = np.percentile(d, 30), np.percentile(d, 72)
    for y, x, dist in zip(ys, xs, d):
        color = ramp[2] if dist <= lo else (ramp[0] if dist > hi else ramp[1])
        canvas[y, x, :3] = color
        canvas[y, x, 3] = 255


def _ellipse_mask(h: int, w: int, cy: float, cx: float, ry: float, rx: float) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w]
    return ((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2 <= 1.0


def make_character(rng: np.random.Generator, width: int = 16, height: int = 24) -> np.ndarray:
    """Symmetric character-like sprite: head + torso + legs, 2-3 ramps, outlined."""
    canvas = np.zeros((height, width, 4), dtype=np.uint8)
    cx = width / 2 - 0.5

    head_r = rng.uniform(0.16, 0.22) * height
    torso_h = rng.uniform(0.34, 0.44) * height
    head_cy = head_r + 1
    skin = make_ramp(rng, hue=float(rng.uniform(0.05, 0.11)))
    cloth = make_ramp(rng)
    boots = make_ramp(rng) if rng.random() < 0.5 else None

    head = _ellipse_mask(height, width, head_cy, cx, head_r, head_r * rng.uniform(0.85, 1.0))
    _shade_region(canvas, head, skin)

    t0 = int(head_cy + head_r)
    t1 = min(height - 2, int(t0 + torso_h))
    half_w = rng.uniform(0.28, 0.42) * width
    torso = np.zeros((height, width), dtype=bool)
    torso[t0:t1, int(cx - half_w) : int(cx + half_w) + 1] = True
    _shade_region(canvas, torso & ~head, cloth)

    leg_w = max(2, int(half_w * 0.55))
    legs = np.zeros((height, width), dtype=bool)
    legs[t1 : height - 1, int(cx - half_w) : int(cx - half_w) + leg_w] = True
    legs[t1 : height - 1, int(cx + half_w) - leg_w + 1 : int(cx + half_w) + 1] = True
    _shade_region(canvas, legs & ~torso & ~head, boots or cloth)

    # enforce left-right symmetry (characters read symmetric front-on)
    left = canvas[:, : width // 2]
    canvas[:, width - width // 2 :] = left[:, ::-1]

    _apply_outline(canvas)
    _add_eyes(canvas, rng, head_cy, cx, head_r)
    return canvas


def _apply_outline(canvas: np.ndarray) -> None:
    vis = canvas[..., 3] >= 128
    h, w = vis.shape
    for y in range(h):
        for x in range(w):
            if not vis[y, x]:
                continue
            on_edge = (
                y in (0, h - 1)
                or x in (0, w - 1)
                or not vis[y - 1, x]
                or not vis[y + 1, x]
                or not vis[y, x - 1]
                or not vis[y, x + 1]
            )
            if on_edge:
                canvas[y, x, :3] = _outline_color(tuple(int(v) for v in canvas[y, x, :3]))


def _add_eyes(canvas: np.ndarray, rng: np.random.Generator, head_cy: float, cx: float, head_r: float) -> None:
    ey = int(head_cy)
    off = max(1, int(head_r * 0.45))
    dark = (16, 16, 24)
    for ex in (int(cx - off), int(cx + off)):
        if 0 <= ey < canvas.shape[0] and 0 <= ex < canvas.shape[1] and canvas[ey, ex, 3] >= 128:
            canvas[ey, ex, :3] = dark


def make_tile(rng: np.random.Generator, size: int = 16) -> np.ndarray:
    """Seamlessly tiling texture tile — generated in wrapped space so every
    edge matches its opposite edge by construction."""
    ramp = make_ramp(rng)
    noise = rng.random((size, size))
    for _ in range(2):  # wrapped smoothing keeps the seams seamless
        noise = sum(np.roll(np.roll(noise, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9.0
    canvas = np.zeros((size, size, 4), dtype=np.uint8)
    lo, hi = np.percentile(noise, 33), np.percentile(noise, 78)
    for y in range(size):
        for x in range(size):
            v = noise[y, x]
            canvas[y, x, :3] = ramp[0] if v <= lo else (ramp[2] if v > hi else ramp[1])
            canvas[y, x, 3] = 255
    return canvas


def build_corpus(
    n_characters: int = 320,
    n_tiles: int = 80,
    out_dir: Path | None = None,
    manifest_path: Path | None = None,
    seed: int = 7,
) -> list[Path]:
    """Generate the Tier 0 corpus with provenance-first writes."""
    rng = np.random.default_rng(seed)
    out = Path(out_dir or DEFAULT_DIR)
    paths: list[Path] = []
    specs = [("char", i) for i in range(n_characters)] + [("tile", i) for i in range(n_tiles)]
    for kind, i in specs:
        sprite_id = f"t0_{kind}_{i:05d}"
        if provenance.has(sprite_id, manifest_path):
            paths.append(out / f"{sprite_id}.png")
            continue
        provenance.append(
            {
                "sprite_id": sprite_id,
                "source_url": "procedural://am-pixel/validation_corpus",
                "creator": "AM Pixel validation_corpus.py",
                "license": "synthetic-validation",
                "license_url": "",
                "date_added": _dt.date.today().isoformat(),
                "perceptual_hash": f"seed{seed}:{kind}:{i}",
                "copyright_filter_status": "not_applicable_synthetic",
                "tier": 0,
            },
            manifest_path,
        )
        if kind == "char":
            h = int(rng.choice([16, 24]))
            arr = make_character(rng, width=16, height=h)
        else:
            arr = make_tile(rng, size=16)
        p = out / f"{sprite_id}.png"
        save_rgba(arr, p)
        paths.append(p)
    return paths


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Build the Tier 0 validation corpus (CHANGE-037)")
    p.add_argument("--characters", type=int, default=320)
    p.add_argument("--tiles", type=int, default=80)
    p.add_argument("--seed", type=int, default=7)
    args = p.parse_args()
    paths = build_corpus(args.characters, args.tiles, seed=args.seed)
    print(f"validation corpus: {len(paths)} sprites in {DEFAULT_DIR}")


if __name__ == "__main__":
    main()
