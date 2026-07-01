"""
Conditioning encoders (CHANGE-032 mechanism 2; prefix method per SPEC §3.4
Risk B — cross-attention is the documented upgrade path, not built until the
Phase 4 measurement demands it).

PaletteChannelEncoder grounds every PAL slot in its actual color: the slot
embedding is the sum of three learned embeddings over the SNES 5-bit channels
(32 values each). DNA conditioning (Modes 1-6) extends the prefix with
categorical construction-rule embeddings; Mode 7 freeform uses the palette
block alone.
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch
import torch.nn as nn

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from model.architecture.config import ModelConfig  # noqa: E402

LIGHT_SOURCES = ("top-left", "top-right", "bottom-left", "bottom-right")


class PaletteChannelEncoder(nn.Module):
    """(B, L, 3) r5/g5/b5 channel ids -> (B, L, d) color embeddings.
    Zero-channels (non-PAL slots) contribute a learned 'no color' offset only."""

    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.r = nn.Embedding(32, cfg.d_model)
        self.g = nn.Embedding(32, cfg.d_model)
        self.b = nn.Embedding(32, cfg.d_model)

    def forward(self, channels: torch.Tensor) -> torch.Tensor:
        return self.r(channels[..., 0]) + self.g(channels[..., 1]) + self.b(channels[..., 2])


class DNAConditioner(nn.Module):
    """Optional DNA construction-rule embedding appended to the prefix
    (one token). Categorical fields only for MVP; the palette itself is
    already grounded by the PAL block."""

    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.light = nn.Embedding(len(LIGHT_SOURCES), cfg.d_model)
        self.max_shades = nn.Embedding(8, cfg.d_model)

    def forward(self, light_source: torch.Tensor, max_shades: torch.Tensor) -> torch.Tensor:
        return self.light(light_source) + self.max_shades(max_shades.clamp(0, 7))


def light_source_id(name: str) -> int:
    try:
        return LIGHT_SOURCES.index(name)
    except ValueError:
        return 0
