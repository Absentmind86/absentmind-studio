"""Shared fixtures: known-good procedural sprites + their anti-pattern corruptions."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))


@pytest.fixture()
def rng() -> np.random.Generator:
    return np.random.default_rng(42)


@pytest.fixture()
def good_character(rng) -> np.ndarray:
    from data.pipeline.validation_corpus import make_character

    return make_character(rng, 16, 24)


@pytest.fixture()
def good_tile(rng) -> np.ndarray:
    from data.pipeline.validation_corpus import make_tile

    return make_tile(rng, 16)
