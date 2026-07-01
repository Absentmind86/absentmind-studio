"""Project character comparison sheet (SPEC §7.1 Check 2) — all characters
side by side at 1x on a neutral checker background, labeled row of sprites."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import alpha_mask, load_rgba, save_rgba  # noqa: E402

PAD = 4
BG = ((44, 44, 52), (52, 52, 62))  # subtle checker so silhouettes read


def build(sprites: dict[str, np.ndarray], out_path: Path | str) -> np.ndarray:
    if not sprites:
        raise ValueError("no sprites given")
    max_h = max(a.shape[0] for a in sprites.values())
    total_w = sum(a.shape[1] for a in sprites.values()) + PAD * (len(sprites) + 1)
    h = max_h + PAD * 2
    sheet = np.zeros((h, total_w, 4), dtype=np.uint8)
    for y in range(h):
        for x in range(total_w):
            sheet[y, x, :3] = BG[((y // 4) + (x // 4)) % 2]
            sheet[y, x, 3] = 255
    x = PAD
    for _name, arr in sorted(sprites.items()):
        ah, aw = arr.shape[:2]
        y0 = h - PAD - ah  # baseline-aligned: characters stand on the same ground
        m = alpha_mask(arr)
        region = sheet[y0 : y0 + ah, x : x + aw]
        region[m] = arr[m]
        x += aw + PAD
    save_rgba(sheet, out_path)
    return sheet


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("sprites", nargs="+")
    p.add_argument("--out", default="comparison_sheet.png")
    args = p.parse_args()
    build({Path(s).stem: load_rgba(s) for s in args.sprites}, args.out)
    print(f"comparison sheet -> {args.out}")


if __name__ == "__main__":
    main()
