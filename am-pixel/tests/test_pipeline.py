"""Data pipeline: indexing canonicality, classification, reorder roundtrip,
provenance safety, splits, view pairs, extraction."""

from __future__ import annotations

import numpy as np
import pytest

from data.pipeline import provenance
from data.pipeline.extractor import extract_auto, extract_grid
from data.pipeline.indexer import index_sprite
from data.pipeline.pixel_classifier import CATEGORY_NAMES_4, category_distribution, classify
from data.pipeline.sequence_reorderer import reconstruct, reorder
from data.pipeline.splitter import split_of
from data.pipeline.view_pair_detector import detect_pairs
from tools._common import TRANSPARENT_INDEX


def test_index_roundtrip_exact(good_character):
    s = index_sprite(good_character)
    assert np.array_equal(s.to_rgba(), good_character)


def test_canonical_palette_is_deterministic(good_character):
    a = index_sprite(good_character)
    b = index_sprite(good_character[:, ::-1].copy())  # mirrored sprite, same colors
    assert a.palette == b.palette  # canonical order ignores pixel positions


def test_reorder_reconstruct_inverse(good_character):
    s = index_sprite(good_character)
    seq = reorder(s)
    assert len(seq) == s.grid.size
    assert np.array_equal(reconstruct(seq), s.grid)
    # structure-aware order: all transparent first, then outline
    cats = seq.categories
    first_visible = int(np.argmax(cats > 0))
    assert np.all(cats[:first_visible] == 0)
    assert cats[first_visible] == 1


def test_classification_covers_all_categories(good_character):
    s = index_sprite(good_character)
    dist = category_distribution(classify(s))
    assert set(dist) == set(CATEGORY_NAMES_4)
    assert dist["transparent"] > 0 and dist["outline"] > 0 and dist["structural"] > 0


def test_npz_roundtrip(tmp_path, good_character):
    from tools._common import IndexedSprite

    s = index_sprite(good_character, meta={"sprite_id": "x1", "tier": 0})
    p = tmp_path / "s.npz"
    s.save_npz(p)
    s2 = IndexedSprite.load_npz(p)
    assert s2.palette == s.palette
    assert np.array_equal(s2.grid, s.grid)
    assert s2.meta["sprite_id"] == "x1"


def test_provenance_policy(tmp_path):
    mp = tmp_path / "M.json"
    e = {"sprite_id": "a", "source_url": "u", "creator": "c", "license": "CC0",
         "date_added": "2026-07-01", "tier": 2}
    provenance.append(e, mp)
    with pytest.raises(ValueError):
        provenance.append(e, mp)  # duplicate
    with pytest.raises(ValueError):
        provenance.append({**e, "sprite_id": "b", "license": "CC-BY-SA"}, mp)  # legal hold
    with pytest.raises(ValueError):
        provenance.append({**e, "sprite_id": "c", "tier": 0}, mp)  # tier 0 needs synthetic license
    provenance.append({**e, "sprite_id": "d", "license": "synthetic-validation", "tier": 0}, mp)
    assert [x["sprite_id"] for x in provenance.production_entries(mp)] == ["a"]


def test_provenance_journal_recovery(tmp_path):
    mp = tmp_path / "M.json"
    for sid in ("a", "b", "c"):
        provenance.append(
            {"sprite_id": sid, "source_url": "u", "creator": "c", "license": "CC0",
             "date_added": "2026-07-01", "tier": 2}, mp)
    mp.write_text("{corrupted")
    assert provenance.rebuild_from_journal(mp) == 3
    assert provenance.has("b", mp)


def test_split_deterministic_and_pair_aware():
    assert split_of("sprite_1") == split_of("sprite_1")
    assert split_of("x", view_pair_id="vp_9") == split_of("y", view_pair_id="vp_9")
    frac = sum(split_of(f"s{i}") == "validation" for i in range(2000)) / 2000
    assert 0.06 < frac < 0.14  # ~10%


def test_extract_grid_and_auto(good_character):
    sheet = np.zeros((24, 64, 4), dtype=np.uint8)
    sheet[:, 0:16] = good_character
    sheet[:, 32:48] = good_character
    cells = extract_grid(sheet, 16, 24)
    assert len(cells) == 2
    autos = extract_auto(sheet, min_area=20)
    assert len(autos) == 2


def test_view_pair_detector_finds_mirror(good_character):
    # procedural characters are symmetric, so break symmetry first (a symmetric
    # sprite's mirror is a duplicate frame and is correctly NOT a view pair)
    asym = good_character.copy()
    ys, xs = np.nonzero(asym[..., 3] >= 128)
    right = xs > asym.shape[1] // 2
    for y, x in list(zip(ys[right], xs[right]))[:14]:
        asym[y, x, 3] = 0  # carve pixels off the right side
    a = index_sprite(asym)
    b = index_sprite(asym[:, ::-1].copy())
    pairs = detect_pairs({"hero_left": a, "hero_right": b})
    assert any(p.kind == "mirror" for p in pairs), pairs
    # unrelated sprite is not paired
    rng = np.random.default_rng(3)
    from data.pipeline.validation_corpus import make_character

    c = index_sprite(make_character(rng, 16, 24))
    assert not detect_pairs({"hero": a, "other": c})
