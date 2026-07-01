"""
Sprite generation — three-phase palette-masked autoregressive sampling.

Phase 1 (mask):     raster scan of all H*W positions; sample TRANSPARENT/OPQ.
Phase 2 (outline):  positions derived from the committed mask; sample palette indices.
Phase 3 (interior): remaining visible positions; sample palette indices.

Palette masking: at phases 2-3 the logits of every id outside 1..n_palette are
set to -inf — the literal implementation of "the model cannot generate a color
that isn't in the palette" (SPEC §3.1). DNA modes pass the DNA palette;
freeform passes any palette up to 256 colors.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from model.architecture.config import (  # noqa: E402
    BOS_ID,
    OPQ_ID,
    PAL_ID,
    PHASE_COND,
    PHASE_INTERIOR,
    PHASE_MASK,
    PHASE_OUTLINE,
    SEP_ID,
    TRANSPARENT_ID,
)
from model.architecture.transformer import PixelTransformer, load_checkpoint  # noqa: E402
from model.architecture.tokenizer import mask_to_outline_interior  # noqa: E402
from tools._common import IndexedSprite  # noqa: E402


@torch.no_grad()
def generate_sprite(
    model: PixelTransformer,
    palette: list[tuple[int, int, int]],
    width: int,
    height: int,
    *,
    temperature: float = 0.9,
    top_k: int = 0,
    seed: int | None = None,
    device: torch.device | str = "cpu",
) -> IndexedSprite:
    if seed is not None:
        torch.manual_seed(seed)
    model.eval()
    n_pal = len(palette)

    values = [BOS_ID] + [PAL_ID] * n_pal + [SEP_ID]
    xs = [0] * len(values)
    ys = [0] * len(values)
    phases = [PHASE_COND] * len(values)
    channels = [(0, 0, 0)] + [(r >> 3, g >> 3, b >> 3) for (r, g, b) in palette] + [(0, 0, 0)]

    def step(x: int, y: int, phase: int, allowed_ids: list[int]) -> int:
        xs.append(x)
        ys.append(y)
        phases.append(phase)
        channels.append((0, 0, 0))
        values.append(TRANSPARENT_ID)  # placeholder; forward uses shifted values
        t = torch.tensor
        logits = model(
            t([values], device=device),
            t([xs], device=device),
            t([ys], device=device),
            t([phases], device=device),
            t([channels], device=device),
        )[0, -1]
        mask = torch.full_like(logits, float("-inf"))
        mask[allowed_ids] = 0.0
        logits = logits / max(temperature, 1e-4) + mask
        if top_k:
            kth = torch.topk(logits, min(top_k, len(allowed_ids))).values[-1]
            logits[logits < kth] = float("-inf")
        choice = int(torch.multinomial(torch.softmax(logits, -1), 1))
        values[-1] = choice
        return choice

    # phase 1 — silhouette
    mask_grid = np.zeros((height, width), dtype=bool)
    for y in range(height):
        for x in range(width):
            v = step(x, y, PHASE_MASK, [TRANSPARENT_ID, OPQ_ID])
            mask_grid[y, x] = v == OPQ_ID

    palette_ids = list(range(1, n_pal + 1))
    outline_pos, interior_pos = mask_to_outline_interior(mask_grid)

    grid = np.zeros((height, width), dtype=np.int16)
    for (x, y) in outline_pos:  # phase 2 — outline
        grid[y, x] = step(x, y, PHASE_OUTLINE, palette_ids)
    for (x, y) in interior_pos:  # phase 3 — interior
        grid[y, x] = step(x, y, PHASE_INTERIOR, palette_ids)

    return IndexedSprite(palette=list(palette), grid=grid)


def generate_from_checkpoint(
    checkpoint: Path | str,
    palette: list[tuple[int, int, int]],
    width: int,
    height: int,
    **kw,
) -> IndexedSprite:
    from model.hardware.detector import get_device

    device = get_device()
    model, _ = load_checkpoint(checkpoint, device)
    return generate_sprite(model, palette, width, height, device=device, **kw)


def main() -> None:
    import argparse

    from tools._common import save_rgba

    p = argparse.ArgumentParser(description="Generate a sprite from a checkpoint")
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--width", type=int, default=16)
    p.add_argument("--height", type=int, default=24)
    p.add_argument("--palette", help="comma-separated hex colors; default: sample palette")
    p.add_argument("--seed", type=int)
    p.add_argument("--temperature", type=float, default=0.9)
    args = p.parse_args()

    if args.palette:
        palette = [
            tuple(int(h.strip().lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
            for h in args.palette.split(",")
        ]
    else:
        palette = [(48, 32, 32), (136, 88, 64), (200, 136, 88), (32, 48, 88), (72, 96, 152), (136, 160, 208)]
    sprite = generate_from_checkpoint(args.checkpoint, palette, args.width, args.height,
                                      seed=args.seed, temperature=args.temperature)
    save_rgba(sprite.to_rgba(), args.out)
    print(f"generated {args.width}x{args.height} -> {args.out}")


if __name__ == "__main__":
    main()
