"""Godot 4.x export: SpriteFrames .tres resource + PNG (SPEC §11)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

DEFAULT_FPS = 8.0


def export(sheet_manifest: dict, sheet_png: Path | str, out_dir: Path | str, fps: float = DEFAULT_FPS) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    name = f"{sheet_manifest['character_id']}_{sheet_manifest['profile']}"
    shutil.copyfile(sheet_png, out / f"{name}.png")

    cw, ch = sheet_manifest["cell_w"], sheet_manifest["cell_h"]
    animations: dict[str, list[dict]] = {}
    for f in sheet_manifest["frames"]:
        if f.get("status", "active") == "active":
            animations.setdefault(f["animation"], []).append(f)

    lines = [
        f'[gd_resource type="SpriteFrames" load_steps={2 + sum(len(v) for v in animations.values())} format=3]',
        "",
        f'[ext_resource type="Texture2D" path="res://{name}.png" id="1"]',
        "",
    ]
    sub_id = 0
    frame_refs: dict[str, list[str]] = {}
    for anim, frames in sorted(animations.items()):
        frame_refs[anim] = []
        for f in sorted(frames, key=lambda fr: fr["frame_index"]):
            sub_id += 1
            sid = f"AtlasTexture_{sub_id}"
            x, y = f["col"] * cw, f["row"] * ch
            lines += [
                f'[sub_resource type="AtlasTexture" id="{sid}"]',
                'atlas = ExtResource("1")',
                f"region = Rect2({x}, {y}, {cw}, {ch})",
                "",
            ]
            frame_refs[anim].append(sid)

    lines.append("[resource]")
    anim_entries = []
    for anim, refs in sorted(frame_refs.items()):
        frames_str = ", ".join(
            '{{"duration": 1.0, "texture": SubResource("{}")}}'.format(r) for r in refs
        )
        anim_entries.append(
            '{{"frames": [{}], "loop": true, "name": &"{}", "speed": {}}}'.format(frames_str, anim, fps)
        )
    lines.append("animations = [" + ", ".join(anim_entries) + "]")

    path = out / f"{name}.tres"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
