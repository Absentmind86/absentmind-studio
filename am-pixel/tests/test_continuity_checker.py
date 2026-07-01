"""continuity_checker: palette family, unique-color cap, scene placement."""

from __future__ import annotations

import numpy as np

from tools import continuity_checker
from tools._common import save_rgba, unique_colors


def test_check1_with_master_palette(good_character):
    master = set(unique_colors(good_character))
    ok, unlisted, problems = continuity_checker.check1_palette_family(good_character, master=master)
    assert ok and not unlisted

    bad = good_character.copy()
    ys, xs = np.nonzero(bad[..., 3] >= 128)
    bad[ys[0], xs[0], :3] = (8, 248, 8)
    ok, unlisted, problems = continuity_checker.check1_palette_family(bad, master=master)
    assert not ok and (8, 248, 8) in unlisted
    # ...unless formally designated character-unique
    ok, unlisted, _ = continuity_checker.check1_palette_family(bad, declared_unique=[(8, 248, 8)], master=master)
    assert ok


def test_unique_color_cap(good_character):
    master = set(unique_colors(good_character))
    ok, _, problems = continuity_checker.check1_palette_family(
        good_character, declared_unique=[(8, 8, 8), (16, 16, 16), (24, 24, 24)], master=master
    )
    assert not ok and any("exceeds max" in p for p in problems)


def test_check3_scene_placement(good_character, good_tile):
    ok, contrast = continuity_checker.check3_scene_placement(good_character, good_tile)
    assert contrast > 0
    # placing the sprite on a tile made of its own colors must fail readability
    self_tile = good_character[8:16, 4:12].copy()
    self_tile[..., 3] = 255
    ok_self, c_self = continuity_checker.check3_scene_placement(good_character, self_tile)
    assert c_self < contrast


def test_run_all_writes_comparison_sheet(tmp_path, good_character, good_tile, rng):
    from data.pipeline.validation_corpus import make_character

    sprite_path = tmp_path / "hero.png"
    save_rgba(good_character, sprite_path)
    out = tmp_path / "cmp.png"
    continuity_checker.run_all(
        sprite_path,
        project_sprites={"other": make_character(rng, 16, 24)},
        representative_tile=good_tile,
        comparison_out=out,
    )
    assert out.is_file()
