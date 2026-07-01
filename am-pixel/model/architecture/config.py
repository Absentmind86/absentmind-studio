"""Model hyperparameters. `small` is the CPU-viable proof-of-life config;
`base` is the Phase 4 production target (GPU)."""

from __future__ import annotations

from dataclasses import asdict, dataclass


# token id layout: 0 = transparent, 1..255 = palette indices,
# then specials (kept contiguous after the palette range)
TRANSPARENT_ID = 0
MAX_PALETTE_ID = 255
BOS_ID = 256
SEP_ID = 257
PAL_ID = 258  # palette-descriptor slot marker (value embedded via channel embeddings)
OPQ_ID = 259  # phase-A opaque placeholder (mask token)
VOCAB_SIZE = 260

# generation phases (also used as segment/phase embedding ids)
PHASE_COND = 0
PHASE_MASK = 1
PHASE_OUTLINE = 2
PHASE_INTERIOR = 3
N_PHASES = 4


@dataclass
class ModelConfig:
    d_model: int = 128
    n_head: int = 4
    n_layer: int = 4
    d_ff: int = 512
    dropout: float = 0.1
    max_canvas: int = 64  # X/Y embedding tables (SPEC MVP canvas cap; freeform larger post-MVP)
    max_palette_slots: int = 16  # 15 colors + transparent (SNES)
    max_seq_len: int = 8320  # cond block + H*W mask tokens + visible tokens at 64x64

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ModelConfig":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


def small() -> ModelConfig:
    return ModelConfig()


def base() -> ModelConfig:
    return ModelConfig(d_model=384, n_head=6, n_layer=10, d_ff=1536, dropout=0.1)
