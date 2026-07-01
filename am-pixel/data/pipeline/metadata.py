"""Structured metadata for training examples — stored inside each IndexedSprite's
meta dict and mirrored in corpus stats. Kept as plain dicts for npz/JSON portability."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class SpriteMetadata:
    sprite_id: str
    tier: int  # 0 validation / 1 golden / 2 broad (SPEC §15)
    width: int
    height: int
    n_colors: int
    genre: str = "unknown"
    platform: str = "unknown"
    asset_type: str = "character"  # character|enemy|tile|ui|effect|font
    quality_estimate: float = 0.0  # 0..1, scraper-side heuristic
    view_pair_id: str | None = None  # CHANGE-017
    view_direction: str | None = None  # front|back|left|right
    synthetic_pair: bool = False  # reflection-generated pair (lower weight)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "SpriteMetadata":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})
