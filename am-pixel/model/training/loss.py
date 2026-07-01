"""Next-token loss over sprite positions (conditioning/padding ignored)."""

from __future__ import annotations

import torch
import torch.nn.functional as F

IGNORE_INDEX = -100


def next_token_loss(logits: torch.Tensor, targets: torch.Tensor, label_smoothing: float = 0.0) -> torch.Tensor:
    return F.cross_entropy(
        logits.reshape(-1, logits.size(-1)),
        targets.reshape(-1),
        ignore_index=IGNORE_INDEX,
        label_smoothing=label_smoothing,
    )


@torch.no_grad()
def token_accuracy(logits: torch.Tensor, targets: torch.Tensor) -> float:
    mask = targets != IGNORE_INDEX
    if not mask.any():
        return 0.0
    pred = logits.argmax(-1)
    return float((pred[mask] == targets[mask]).float().mean())
