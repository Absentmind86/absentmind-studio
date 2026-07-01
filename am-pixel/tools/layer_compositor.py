"""
Parallax layer composition and evaluation (SPEC §5.3b, Rubric C).

Assembles layers back-to-front at multiple scroll offset ratios, verifies:
- horizontal wrap seamlessness per layer (Layer Seaming)
- depth separation: nearer layers should carry more detail/contrast than
  farther ones (Layer Depth Differentiation)
- character contrast: a sprite composited at center must stand out from
  the background behind it (Character Contrast)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import alpha_mask, load_rgba, save_rgba  # noqa: E402
from tools.tileset_anchor_extractor import _detail_density  # noqa: E402

DEFAULT_RATIOS = (0.0, 0.25, 0.5, 0.75)  # scroll phases to test


def composite(layers: list[np.ndarray], scroll_phase: float = 0.0) -> np.ndarray:
    """Composite layers back (index 0) to front, each scrolled horizontally by
    phase * (its parallax factor), wrapping. Layer i scrolls at i/(n-1) speed."""
    base = layers[0]
    h, w = base.shape[:2]
    out = np.zeros((h, w, 4), dtype=np.uint8)
    n = len(layers)
    for i, layer in enumerate(layers):
        speed = i / max(n - 1, 1)
        shift = int(round(scroll_phase * speed * w)) % w
        rolled = np.roll(layer, -shift, axis=1)
        lh = rolled.shape[0]
        y0 = h - lh  # layers anchor to the bottom (horizon composition)
        region = out[max(y0, 0) : h]
        src = rolled[max(-y0, 0) :]
        m = alpha_mask(src)
        region[m] = src[m]
    return out


@dataclass
class ParallaxReport:
    ok: bool
    layer_seam_ratios: list[float] = field(default_factory=list)
    depth_monotonic: bool = True
    detail_by_layer: list[float] = field(default_factory=list)
    character_contrast: float | None = None
    problems: list[str] = field(default_factory=list)


def evaluate(
    layers: list[np.ndarray],
    *,
    character: np.ndarray | None = None,
    seam_max_ratio: float = 1.8,
    min_character_contrast: float = 40.0,
) -> ParallaxReport:
    from tools.seam_validator import _internal_change, _row_change

    report = ParallaxReport(ok=True)

    for i, layer in enumerate(layers):
        v = layer.transpose(1, 0, 2)
        seam = _row_change(v[-1], v[0])
        ratio = seam / _internal_change(layer)
        report.layer_seam_ratios.append(round(ratio, 3))
        if ratio > seam_max_ratio:
            report.ok = False
            report.problems.append(f"layer {i} horizontal wrap seam visible (ratio {ratio:.2f})")

    report.detail_by_layer = [round(_detail_density(l), 4) for l in layers]
    # detail should not *decrease* toward the foreground
    for i in range(1, len(report.detail_by_layer)):
        if report.detail_by_layer[i] < report.detail_by_layer[i - 1] * 0.6:
            report.depth_monotonic = False
            report.ok = False
            report.problems.append(
                f"layer {i} (nearer) has much less detail than layer {i - 1} — depth reads inverted"
            )
            break

    if character is not None:
        comp = composite(layers, 0.0)
        ch, cw = character.shape[:2]
        h, w = comp.shape[:2]
        y0, x0 = (h - ch) // 2, (w - cw) // 2
        bg = comp[y0 : y0 + ch, x0 : x0 + cw, :3].astype(float)
        m = alpha_mask(character)
        fg = character[..., :3].astype(float)
        contrast = float(np.abs(fg[m] - bg[m]).mean()) if m.any() else 0.0
        report.character_contrast = round(contrast, 2)
        if contrast < min_character_contrast:
            report.ok = False
            report.problems.append(
                f"character contrast {contrast:.0f} below {min_character_contrast:.0f} — sprite does not read against background"
            )
    return report


def render_scroll_strip(layers: list[np.ndarray], out_path: Path | str, ratios=DEFAULT_RATIOS) -> None:
    """Side-by-side composites at several scroll phases for human review."""
    frames = [composite(layers, r) for r in ratios]
    strip = np.concatenate(frames, axis=1)
    save_rgba(strip, out_path)


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("layers", nargs="+", help="back-to-front layer PNGs")
    p.add_argument("--strip", help="write scroll test strip PNG here")
    args = p.parse_args()
    layers = [load_rgba(l) for l in args.layers]
    rep = evaluate(layers)
    print("OK" if rep.ok else "; ".join(rep.problems))
    if args.strip:
        render_scroll_strip(layers, args.strip)


if __name__ == "__main__":
    main()
