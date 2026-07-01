"""
Deterministic train/validation split (90/10 per ROADMAP Phase 3).

Hash-based on sprite_id so the split is stable across runs and machines —
re-running the pipeline never moves a sprite between splits, and view-pair
members stay together (pair id is hashed when present, so both views of a
pair land in the same split and the model is never validated on a pair
whose sibling it trained on).
"""

from __future__ import annotations

import hashlib


def split_of(sprite_id: str, view_pair_id: str | None = None, validation_fraction: float = 0.10) -> str:
    key = view_pair_id or sprite_id
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:4], "big") / 0xFFFFFFFF
    return "validation" if bucket < validation_fraction else "train"


def split_all(entries: list[dict], validation_fraction: float = 0.10) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {"train": [], "validation": []}
    for e in entries:
        out[split_of(e["sprite_id"], e.get("view_pair_id"), validation_fraction)].append(e)
    return out
