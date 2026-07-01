"""
DNA extraction from an approved master sprite (SPEC §4.4).

Produces the DNA JSON (schema per SPEC §4.2), writes the versioned file
dna/characters/[character_id]_vN.json, and appends to CONTINUITY_MANIFEST.md.
Version N = approved master design count (CHANGE-029): extract() never
overwrites an existing version — it writes the next one.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import sys
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import alpha_mask, cluster_ramps, load_rgba, unique_colors  # noqa: E402
from tools.outline_checker import _outline_pixels  # noqa: E402

DNA_DIR = _AM_PIXEL / "dna" / "characters"
MANIFEST = _AM_PIXEL / "dna" / "CONTINUITY_MANIFEST.md"


def _estimate_light_source(rgba: np.ndarray) -> str:
    """Compare the centroid of the lightest ramp steps vs the darkest: if the
    highlight centroid sits up-left of the shadow centroid, light is top-left."""
    colors = unique_colors(rgba)
    if len(colors) < 3:
        return "top-left"
    by_v = sorted(colors, key=sum)
    dark, light = set(by_v[: max(1, len(by_v) // 3)]), set(by_v[-max(1, len(by_v) // 3) :])
    vis = alpha_mask(rgba)
    pts = {"dark": [], "light": []}
    for y, x in zip(*np.nonzero(vis)):
        rgb = tuple(int(v) for v in rgba[y, x, :3])
        if rgb in dark:
            pts["dark"].append((y, x))
        elif rgb in light:
            pts["light"].append((y, x))
    if not pts["dark"] or not pts["light"]:
        return "top-left"
    dy = float(np.mean([p[0] for p in pts["light"]]) - np.mean([p[0] for p in pts["dark"]]))
    dx = float(np.mean([p[1] for p in pts["light"]]) - np.mean([p[1] for p in pts["dark"]]))
    v = "top" if dy <= 0 else "bottom"
    h = "left" if dx <= 0 else "right"
    return f"{v}-{h}"


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _next_version(character_id: str, dna_dir: Path) -> int:
    pattern = re.compile(rf"^{re.escape(character_id)}_v(\d+)\.json$")
    versions = [
        int(m.group(1))
        for f in dna_dir.glob(f"{character_id}_v*.json")
        if (m := pattern.match(f.name))
    ]
    return max(versions, default=0) + 1


def extract(
    master_sprite_path: Path | str,
    *,
    character_id: str,
    character_name: str,
    brief: dict | None = None,
    profiles: dict | None = None,
    master_profile: str = "world_sprite",
    continuity_group: str = "default",
    master_palette_colors: set[tuple[int, int, int]] | None = None,
    dna_dir: Path | None = None,
) -> dict:
    """Extract DNA from the approved master sprite. Returns the DNA dict
    (already written to dna/characters/[id]_vN.json)."""
    rgba = load_rgba(master_sprite_path)
    h, w = rgba.shape[:2]
    colors = unique_colors(rgba)
    ramps = cluster_ramps(colors)

    palette: dict[str, str] = {}
    for ri, ramp in enumerate(ramps):
        names = ["shadow", "base", "highlight"]
        for ci, c in enumerate(ramp):
            level = names[ci] if len(ramp) <= 3 else f"step{ci}"
            palette[f"ramp{ri}_{level}"] = _hex(c)

    outline_colors = sorted(
        {_hex(tuple(int(v) for v in rgba[y, x, :3])) for (x, y) in _outline_pixels(rgba)}
    )
    unique = (
        [_hex(c) for c in colors if c not in master_palette_colors]
        if master_palette_colors is not None
        else []
    )

    dna_dir = dna_dir or DNA_DIR
    version = _next_version(character_id, dna_dir) if dna_dir.exists() else 1

    dna = {
        "character_id": character_id,
        "character_name": character_name,
        "approved_date": _dt.date.today().isoformat(),
        "version": version,
        "brief": brief
        or {"personality": "", "role": "", "defining_trait": "", "occluded_features": []},
        "profiles": profiles
        or {master_profile: {"width": w, "height": h, "context": "overworld_exploration", "detail_level": "standard"}},
        "palette": palette,
        "construction_rules": {
            "light_source": _estimate_light_source(rgba),
            "outline_style": "darkened_local_color",
            "outline_weight": 1,
            "shading_method": "hue_shifted_ramp",
            "max_shades_per_region": max(len(r) for r in ramps) if ramps else 0,
        },
        "proportion_notes": "",
        "unique_colors": unique,
        "master_profile": master_profile,
        "animation_sets_completed": [],
        "sprite_sheet_path": str(master_sprite_path),
        "continuity_group": continuity_group,
        "github_asset_path": f"assets/characters/{character_id}/",
    }

    dna_dir.mkdir(parents=True, exist_ok=True)
    out = dna_dir / f"{character_id}_v{version}.json"
    out.write_text(json.dumps(dna, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _update_manifest(dna)
    return dna


def _update_manifest(dna: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    if not MANIFEST.is_file():
        MANIFEST.write_text("# Continuity Manifest\n\nMaster tracking for project visual continuity.\n", encoding="utf-8")
    line = (
        f"\n## {dna['character_name']} (`{dna['character_id']}`) v{dna['version']}\n"
        f"- DNA: `dna/characters/{dna['character_id']}_v{dna['version']}.json`\n"
        f"- Light source: {dna['construction_rules']['light_source']}\n"
        f"- Ramps: {len({k.split('_')[0] for k in dna['palette']})} | "
        f"Unique colors: {', '.join(dna['unique_colors']) or 'none'}\n"
        f"- Continuity group: {dna['continuity_group']}\n"
        f"- Status: active\n"
    )
    with MANIFEST.open("a", encoding="utf-8") as f:
        f.write(line)


def dna_palette_rgb(dna: dict) -> list[tuple[int, int, int]]:
    """All RGB colors in a DNA palette (for validators/generation masking)."""
    out = []
    for v in dna["palette"].values():
        out.append(tuple(int(v[i : i + 2], 16) for i in (1, 3, 5)))
    return out


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Extract DNA from an approved master sprite")
    p.add_argument("sprite")
    p.add_argument("--id", required=True)
    p.add_argument("--name", required=True)
    args = p.parse_args()
    dna = extract(args.sprite, character_id=args.id, character_name=args.name)
    print(f"DNA v{dna['version']} written for {args.id} ({len(dna['palette'])} palette entries)")


if __name__ == "__main__":
    main()
