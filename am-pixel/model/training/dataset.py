"""Corpus dataset: indexed .npz sprites -> padded token batches.

Split assignment is deterministic per sprite_id (splitter.py). Targets are
-100 on conditioning slots and padding so the loss covers sprite tokens only."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from data.pipeline.splitter import split_of  # noqa: E402
from model.architecture.tokenizer import TokenizedSprite, tokenize  # noqa: E402
from tools._common import IndexedSprite  # noqa: E402

IGNORE_INDEX = -100


class SpriteDataset(Dataset):
    def __init__(self, corpus_dir: Path | str, split: str = "train"):
        self.files = []
        for f in sorted(Path(corpus_dir).glob("*.npz")):
            sprite_id = f.stem
            if split_of(sprite_id) == split:
                self.files.append(f)
        if not self.files:
            raise ValueError(f"no {split} sprites found in {corpus_dir}")
        self.split = split

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, i: int) -> TokenizedSprite:
        return tokenize(IndexedSprite.load_npz(self.files[i]))


def collate(batch: list[TokenizedSprite]) -> dict[str, torch.Tensor]:
    L = max(len(t.values) for t in batch)
    B = len(batch)
    out = {
        "values": torch.zeros(B, L, dtype=torch.long),
        "xs": torch.zeros(B, L, dtype=torch.long),
        "ys": torch.zeros(B, L, dtype=torch.long),
        "phases": torch.zeros(B, L, dtype=torch.long),
        "channels": torch.zeros(B, L, 3, dtype=torch.long),
        "pad_mask": torch.ones(B, L, dtype=torch.bool),
        "targets": torch.full((B, L), IGNORE_INDEX, dtype=torch.long),
    }
    for b, t in enumerate(batch):
        n = len(t.values)
        out["values"][b, :n] = torch.from_numpy(t.values)
        out["xs"][b, :n] = torch.from_numpy(t.xs)
        out["ys"][b, :n] = torch.from_numpy(t.ys)
        out["phases"][b, :n] = torch.from_numpy(t.phases)
        out["channels"][b, :n] = torch.from_numpy(t.channels)
        out["pad_mask"][b, :n] = False
        tgt = torch.from_numpy(t.values.copy())
        tgt[~torch.from_numpy(t.target_mask)] = IGNORE_INDEX
        out["targets"][b, :n] = tgt
    return out
