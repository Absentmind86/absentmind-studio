"""Generic export: sprite sheet PNG + JSON manifest (SPEC §11 universal fallback)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))


def export(sheet_manifest: dict, sheet_png: Path | str, out_dir: Path | str) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    name = f"{sheet_manifest['character_id']}_{sheet_manifest['profile']}"
    shutil.copyfile(sheet_png, out / f"{name}.png")

    animations: dict[str, list[dict]] = {}
    for f in sheet_manifest["frames"]:
        if f.get("status", "active") != "active":
            continue
        animations.setdefault(f["animation"], []).append(
            {
                "frame_index": f["frame_index"],
                "x": f["col"] * sheet_manifest["cell_w"],
                "y": f["row"] * sheet_manifest["cell_h"],
                "w": sheet_manifest["cell_w"],
                "h": sheet_manifest["cell_h"],
            }
        )
    for frames in animations.values():
        frames.sort(key=lambda fr: fr["frame_index"])

    manifest = {
        "format": "am-pixel-generic-v1",
        "character_id": sheet_manifest["character_id"],
        "profile": sheet_manifest["profile"],
        "image": f"{name}.png",
        "cell_w": sheet_manifest["cell_w"],
        "cell_h": sheet_manifest["cell_h"],
        "animations": animations,
    }
    path = out / f"{name}.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
