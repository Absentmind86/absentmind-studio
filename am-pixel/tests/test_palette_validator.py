"""palette_validator: SNES legality, color caps, out-of-palette coordinates."""

from __future__ import annotations

import numpy as np

from tools import palette_validator
from tools._common import unique_colors


def test_good_sprite_passes(good_character):
    r = palette_validator.validate(good_character)
    assert r.ok, r.summary()


def test_non_snes_color_flagged(good_character):
    bad = good_character.copy()
    ys, xs = np.nonzero(bad[..., 3] >= 128)
    bad[ys[0], xs[0], :3] = (201, 77, 33)  # not multiples of 8
    r = palette_validator.validate(bad)
    assert not r.ok and r.non_snes_colors


def test_out_of_palette_pixel_located(good_character):
    allowed = unique_colors(good_character)
    bad = good_character.copy()
    ys, xs = np.nonzero(bad[..., 3] >= 128)
    y, x = int(ys[5]), int(xs[5])
    bad[y, x, :3] = (8, 248, 8)  # SNES-legal but not in the allowed palette
    r = palette_validator.validate(bad, allowed)
    assert not r.ok
    assert (x, y, (8, 248, 8)) in r.out_of_palette


def test_color_cap():
    arr = np.zeros((8, 32, 4), dtype=np.uint8)
    arr[..., 3] = 255
    for i in range(32):  # 32 distinct colors > 15 cap
        arr[:, i, :3] = (8 * i, 0, 0)
    r = palette_validator.validate(arr)
    assert not r.ok and r.over_color_limit
