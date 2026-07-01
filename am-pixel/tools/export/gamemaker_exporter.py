"""GameMaker export: horizontal PNG strip per animation + JSON frame data (SPEC §11)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import load_rgba, save_rgba  # noqa: E402


def export(sheet_manifest: dict, sheet_png: Path | str, out_dir: Path | str, fps: int = 8) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cw, ch = sheet_manifest["cell_w"], sheet_manifest["cell_h"]
    png = load_rgba(sheet_png)
    name = f"{sheet_manifest['character_id']}_{sheet_manifest['profile']}"

    by_anim: dict[str, list[dict]] = {}
    for f in sheet_manifest["frames"]:
        if f.get("status", "active") == "active":
            by_anim.setdefault(f["animation"], []).append(f)

    data: dict = {"format": "am-pixel-gamemaker-v1", "fps": fps, "frame_w": cw, "frame_h": ch, "strips": {}}
    for anim, frames in sorted(by_anim.items()):
        frames = sorted(frames, key=lambda fr: fr["frame_index"])
        strip = np.zeros((ch, cw * len(frames), 4), dtype=np.uint8)
        for i, f in enumerate(frames):
            sy, sx = f["row"] * ch, f["col"] * cw
            strip[:, i * cw : (i + 1) * cw] = png[sy : sy + ch, sx : sx + cw]
        strip_name = f"{name}_{anim}_strip{len(frames)}.png"
        save_rgba(strip, out / strip_name)
        data["strips"][anim] = {"image": strip_name, "frames": len(frames)}

    path = out / f"{name}.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
