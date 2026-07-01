"""
Core model: decoder-only transformer over palette-index tokens with 2D
learned canvas embeddings (CHANGE-010) and palette-grounded conditioning
(CHANGE-032). No diffusion, no RGB generation — Constitution Rule 2.

Input embedding per slot t (predicting the value at position (x_t, y_t)):

    value_emb(v_{t-1})        previous slot's value (shifted teacher forcing)
    + x_emb(x_t) + y_emb(y_t) 2D position of the token BEING PREDICTED (query)
    + phase_emb(phase_t)      cond / mask / outline / interior segment
    + channel_emb(channels_t) palette color grounding (PAL slots; zeros else)

A standard causal mask runs over the whole sequence (conditioning block
included). Structure-aware ordering is compatible with the causal mask
because position is a query embedding, not implied by slot index — see
IMPLEMENTATION_NOTES.md §3.
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch
import torch.nn as nn

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from model.architecture.conditioning import PaletteChannelEncoder  # noqa: E402
from model.architecture.config import BOS_ID, VOCAB_SIZE, ModelConfig  # noqa: E402


class PixelTransformer(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.cfg = cfg
        self.value_emb = nn.Embedding(VOCAB_SIZE, cfg.d_model)
        self.x_emb = nn.Embedding(cfg.max_canvas, cfg.d_model)
        self.y_emb = nn.Embedding(cfg.max_canvas, cfg.d_model)
        self.phase_emb = nn.Embedding(8, cfg.d_model)
        self.channel_enc = PaletteChannelEncoder(cfg)
        self.drop = nn.Dropout(cfg.dropout)
        layer = nn.TransformerEncoderLayer(
            cfg.d_model, cfg.n_head, cfg.d_ff, cfg.dropout,
            batch_first=True, norm_first=True, activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(layer, cfg.n_layer)
        self.norm = nn.LayerNorm(cfg.d_model)
        self.head = nn.Linear(cfg.d_model, VOCAB_SIZE)

    def forward(
        self,
        values: torch.Tensor,  # (B, L) token ids at each slot
        xs: torch.Tensor,  # (B, L)
        ys: torch.Tensor,  # (B, L)
        phases: torch.Tensor,  # (B, L)
        channels: torch.Tensor,  # (B, L, 3)
        pad_mask: torch.Tensor | None = None,  # (B, L) True at padding
    ) -> torch.Tensor:
        """Returns logits (B, L, V) where logits[:, t] predicts values[:, t]."""
        B, L = values.shape
        prev = torch.cat(
            [torch.full((B, 1), BOS_ID, dtype=values.dtype, device=values.device), values[:, :-1]],
            dim=1,
        )
        h = (
            self.value_emb(prev)
            + self.x_emb(xs)
            + self.y_emb(ys)
            + self.phase_emb(phases)
            + self.channel_enc(channels)
        )
        h = self.drop(h)
        causal = torch.triu(torch.ones(L, L, dtype=torch.bool, device=values.device), diagonal=1)
        h = self.encoder(h, mask=causal, src_key_padding_mask=pad_mask)
        return self.head(self.norm(h))

    def n_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters())


def save_checkpoint(model: PixelTransformer, path: Path | str, step: int, extra: dict | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"config": model.cfg.to_dict(), "state_dict": model.state_dict(), "step": step, **(extra or {})},
        path,
    )


def load_checkpoint(path: Path | str, device: torch.device | str = "cpu") -> tuple[PixelTransformer, dict]:
    ckpt = torch.load(path, map_location=device, weights_only=False)
    cfg = ModelConfig.from_dict(ckpt["config"])
    model = PixelTransformer(cfg).to(device)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    return model, ckpt
