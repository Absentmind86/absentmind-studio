"""Detector calibration: every anti-pattern corruption must be caught on the
corrupted sprite and NOT flagged on the clean original (Phase 5 gate: 90%+)."""

from __future__ import annotations

import numpy as np

from data.antipatterns.generator import (
    corrupt_anti_aliasing,
    corrupt_banding,
    corrupt_black_outline,
)
from data.pipeline.validation_corpus import make_character
from tools import anti_aliasing_detector, banding_detector, outline_checker


def _batch(n=25, seed=7):
    rng = np.random.default_rng(seed)
    return [make_character(rng, 16, 24) for _ in range(n)]


def test_black_outline_detection_rate():
    sprites = _batch()
    caught = sum(not outline_checker.check(corrupt_black_outline(s)).ok for s in sprites)
    false_pos = sum(not outline_checker.check(s).ok for s in sprites)
    assert caught / len(sprites) >= 0.9, f"detection rate {caught}/{len(sprites)}"
    assert false_pos == 0, f"{false_pos} clean sprites falsely flagged"


def test_banding_detection_rate():
    sprites = _batch()
    caught = sum(not banding_detector.check(corrupt_banding(s)).ok for s in sprites)
    false_pos = sum(not banding_detector.check(s).ok for s in sprites)
    assert caught / len(sprites) >= 0.9, f"detection rate {caught}/{len(sprites)}"
    assert false_pos / len(sprites) <= 0.1, f"{false_pos} clean sprites falsely flagged"


def test_anti_aliasing_detection_rate():
    sprites = _batch()
    corrupted = [corrupt_anti_aliasing(s) for s in sprites]
    pairs = [(s, c) for s, c in zip(sprites, corrupted) if not np.array_equal(s, c)]
    assert len(pairs) >= 15, "corruption no-op on too many sprites"
    caught = sum(not anti_aliasing_detector.check(c).ok for _, c in pairs)
    false_pos = sum(not anti_aliasing_detector.check(s).ok for s, _ in pairs)
    assert caught / len(pairs) >= 0.9, f"detection rate {caught}/{len(pairs)}"
    assert false_pos / len(pairs) <= 0.1, f"{false_pos} clean sprites falsely flagged"
