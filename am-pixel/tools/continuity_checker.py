"""
The three continuity checks (SPEC §7.1) — run on every completed sprite.

Check 1 — Palette family compliance: every color traceable to a MASTER_PALETTE
          ramp or formally designated character-unique (max 2 per character;
          portrait-profile-local colors excluded per SPEC §5.1).
Check 2 — Group comparison: regenerate the project comparison sheet.
Check 3 — Scene placement: composite the sprite on a representative tile fill
          and measure readability contrast.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import alpha_mask, load_rgba, unique_colors  # noqa: E402
from tools.comparison_sheet import build as build_comparison  # noqa: E402

MASTER_PALETTE_MD = _AM_PIXEL / "style-bible" / "MASTER_PALETTE.md"
MAX_UNIQUE_COLORS = 2  # per character (SPEC §7.1)
HEX_RE = re.compile(r"#([0-9A-Fa-f]{6})\b")


def load_master_palette(md_path: Path | None = None) -> set[tuple[int, int, int]]:
    """Every #RRGGBB hex code in MASTER_PALETTE.md is a palette family color."""
    path = md_path or MASTER_PALETTE_MD
    if not path.is_file():
        return set()
    out = set()
    for m in HEX_RE.finditer(path.read_text(encoding="utf-8")):
        h = m.group(1)
        out.add(tuple(int(h[i : i + 2], 16) for i in (0, 2, 4)))
    return out


@dataclass
class ContinuityReport:
    ok: bool
    check1_unlisted: list[tuple[int, int, int]] = field(default_factory=list)
    check3_contrast: float | None = None
    problems: list[str] = field(default_factory=list)


def check1_palette_family(
    rgba: np.ndarray,
    declared_unique: list[tuple[int, int, int]] | None = None,
    master: set[tuple[int, int, int]] | None = None,
) -> tuple[bool, list[tuple[int, int, int]], list[str]]:
    master = master if master is not None else load_master_palette()
    declared = set(declared_unique or [])
    problems = []
    if len(declared) > MAX_UNIQUE_COLORS:
        problems.append(f"{len(declared)} character-unique colors exceeds max {MAX_UNIQUE_COLORS}")
    if not master:
        problems.append("MASTER_PALETTE.md defines no colors yet (Phase 2) — check 1 skipped")
        return (not problems, [], problems)
    unlisted = [c for c in unique_colors(rgba) if c not in master and c not in declared]
    if unlisted:
        problems.append(f"{len(unlisted)} colors not in any MASTER_PALETTE ramp and not designated unique")
    return (not problems, unlisted, problems)


def check3_scene_placement(rgba: np.ndarray, tile: np.ndarray, *, min_contrast: float = 40.0) -> tuple[bool, float]:
    ch, cw = rgba.shape[:2]
    ty = int(np.ceil(ch / tile.shape[0]))
    tx = int(np.ceil(cw / tile.shape[1]))
    scene = np.tile(tile, (ty, tx, 1))[:ch, :cw]
    m = alpha_mask(rgba)
    if not m.any():
        return False, 0.0
    contrast = float(np.abs(rgba[..., :3].astype(float)[m] - scene[..., :3].astype(float)[m]).mean())
    return contrast >= min_contrast, round(contrast, 2)


def run_all(
    sprite_path: Path | str,
    *,
    project_sprites: dict[str, np.ndarray] | None = None,
    representative_tile: np.ndarray | None = None,
    declared_unique: list[tuple[int, int, int]] | None = None,
    comparison_out: Path | str | None = None,
) -> ContinuityReport:
    rgba = load_rgba(sprite_path)
    report = ContinuityReport(ok=True)

    ok1, unlisted, problems1 = check1_palette_family(rgba, declared_unique)
    report.check1_unlisted = unlisted
    report.problems += problems1
    hard_failures = [p for p in problems1 if "skipped" not in p]
    if hard_failures:
        report.ok = False

    if project_sprites:
        sprites = dict(project_sprites)
        sprites[Path(sprite_path).stem] = rgba
        build_comparison(sprites, comparison_out or (_AM_PIXEL / "logs" / "comparison_sheet.png"))

    if representative_tile is not None:
        ok3, contrast = check3_scene_placement(rgba, representative_tile)
        report.check3_contrast = contrast
        if not ok3:
            report.ok = False
            report.problems.append(f"scene placement contrast {contrast:.0f} too low — sprite does not read against environment")
    return report


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("sprite")
    p.add_argument("--tile", help="representative tileset tile PNG")
    args = p.parse_args()
    tile = load_rgba(args.tile) if args.tile else None
    r = run_all(args.sprite, representative_tile=tile)
    print("OK" if r.ok else "; ".join(r.problems))


if __name__ == "__main__":
    main()
