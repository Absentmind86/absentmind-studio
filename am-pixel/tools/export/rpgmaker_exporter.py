"""
RPG Maker MZ export (SPEC §11).

MZ character sheets are a fixed 3-column x 4-row block per character
(cols = step frames, rows = down/left/right/up). This exporter re-packs an
AM Pixel sheet's walk animations into that layout. Sheets holding a single
character use the '$' filename prefix so MZ reads them as one block.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import load_rgba, save_rgba  # noqa: E402

MZ_DIRECTIONS = ("walk_down", "walk_left", "walk_right", "walk_up")
MZ_COLS = 3


def export(sheet_manifest: dict, sheet_png: Path | str, out_dir: Path | str) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cw, ch = sheet_manifest["cell_w"], sheet_manifest["cell_h"]
    png = load_rgba(sheet_png)

    by_anim: dict[str, list[dict]] = {}
    for f in sheet_manifest["frames"]:
        if f.get("status", "active") == "active":
            by_anim.setdefault(f["animation"], []).append(f)

    target = np.zeros((4 * ch, MZ_COLS * cw, 4), dtype=np.uint8)
    for row, anim in enumerate(MZ_DIRECTIONS):
        frames = sorted(by_anim.get(anim, []), key=lambda fr: fr["frame_index"])[:MZ_COLS]
        for col, f in enumerate(frames):
            sy, sx = f["row"] * ch, f["col"] * cw
            target[row * ch : (row + 1) * ch, col * cw : (col + 1) * cw] = png[sy : sy + ch, sx : sx + cw]

    path = out / f"${sheet_manifest['character_id']}.png"
    save_rgba(target, path)
    return path
