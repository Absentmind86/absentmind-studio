"""
DNA vs candidate-sprite diff (SPEC §8.4).

Checks a candidate against a DNA record:
- every visible color belongs to the DNA palette (+ declared unique colors)
- dimensions match the declared profile
- outline rule (no pure black) and light-source direction consistency
Produces a violation list, a 0..1 consistency score, and an optional overlay
PNG with deviating pixels marked.

verify_dna_matches_sprite(dna_path, sprite_path) is the entry point
dna_lock_verifier calls after every DNA lock (CHANGE-028 Mechanism 3).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import alpha_mask, load_rgba, save_rgba  # noqa: E402
from tools.dna_extractor import _estimate_light_source, dna_palette_rgb  # noqa: E402
from tools.outline_checker import check as outline_check  # noqa: E402


@dataclass
class DnaDiffReport:
    consistency: float  # 0..1
    violations: list[str] = field(default_factory=list)
    off_palette_pixels: list[tuple[int, int]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations


def diff(dna: dict, rgba: np.ndarray, *, profile: str | None = None) -> DnaDiffReport:
    report = DnaDiffReport(consistency=1.0)
    allowed = set(dna_palette_rgb(dna))
    for hexcol in dna.get("unique_colors", []):
        allowed.add(tuple(int(hexcol[i : i + 2], 16) for i in (1, 3, 5)))

    prof = dna["profiles"].get(profile or dna.get("master_profile", ""), None)
    h, w = rgba.shape[:2]
    if prof and (w != prof["width"] or h != prof["height"]):
        report.violations.append(
            f"dimensions {w}x{h} do not match profile {profile or dna.get('master_profile')} "
            f"({prof['width']}x{prof['height']})"
        )

    vis = alpha_mask(rgba)
    total = int(np.count_nonzero(vis))
    for y, x in zip(*np.nonzero(vis)):
        if tuple(int(v) for v in rgba[y, x, :3]) not in allowed:
            report.off_palette_pixels.append((int(x), int(y)))
    if report.off_palette_pixels:
        frac = len(report.off_palette_pixels) / max(total, 1)
        report.violations.append(
            f"{len(report.off_palette_pixels)} pixels ({frac:.1%}) outside DNA palette"
        )
        report.consistency -= frac

    oc = outline_check(rgba)
    if not oc.ok:
        report.violations.append(oc.summary())
        report.consistency -= 0.1

    want_light = dna.get("construction_rules", {}).get("light_source")
    got_light = _estimate_light_source(rgba)
    if want_light and got_light != want_light:
        report.violations.append(f"light source reads as {got_light}, DNA says {want_light}")
        report.consistency -= 0.1

    report.consistency = max(0.0, round(report.consistency, 4))
    return report


def overlay(rgba: np.ndarray, report: DnaDiffReport, out_path: Path | str) -> None:
    """Write a 4x-scaled overlay PNG with off-palette pixels marked magenta."""
    marked = rgba.copy()
    for x, y in report.off_palette_pixels:
        marked[y, x] = (255, 0, 255, 255)
    big = np.kron(marked, np.ones((4, 4, 1), dtype=np.uint8))
    save_rgba(big, out_path)


def verify_dna_matches_sprite(dna_path: Path | str, sprite_path: Path | str) -> tuple[bool, str]:
    """Post-lock verification entry point (dna_lock_verifier)."""
    dna = json.loads(Path(dna_path).read_text(encoding="utf-8"))
    report = diff(dna, load_rgba(sprite_path))
    if report.ok:
        return True, f"DNA matches sprite (consistency {report.consistency:.2f})"
    return False, "; ".join(report.violations)


def half_consistency(dna: dict, rgba: np.ndarray) -> tuple[float, float]:
    """(top_half, bottom_half) DNA consistency — the CHANGE-008 Phase 4 measurement."""
    h = rgba.shape[0]
    top = diff(dna, rgba[: h // 2]).consistency
    bottom = diff(dna, rgba[h // 2 :]).consistency
    return top, bottom


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("dna_json")
    p.add_argument("sprite")
    p.add_argument("--overlay", help="write deviation overlay PNG here")
    args = p.parse_args()
    dna = json.loads(Path(args.dna_json).read_text(encoding="utf-8"))
    rgba = load_rgba(args.sprite)
    report = diff(dna, rgba)
    print(f"consistency {report.consistency:.2f}; " + ("OK" if report.ok else "; ".join(report.violations)))
    if args.overlay:
        overlay(rgba, report, args.overlay)


if __name__ == "__main__":
    main()
