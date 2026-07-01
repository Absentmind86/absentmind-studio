"""rubric_scorer: gate semantics, evidence requirement, combined failure paths."""

from __future__ import annotations

import numpy as np
import pytest

from data.antipatterns.generator import corrupt_black_outline
from data.pipeline.validation_corpus import make_tile
from tools import rubric_scorer, seam_validator


def test_good_character_passes_automated_gate(good_character):
    r = rubric_scorer.score_rubric_a(good_character)
    assert r["automated_score"] == 85, r["categories"]
    assert r["passed_gate"] and r["evidence_complete"]


def test_corrupted_character_fails_gate(good_character):
    r = rubric_scorer.score_rubric_a(corrupt_black_outline(good_character))
    assert not r["passed_gate"]
    assert r["categories"]["construction_quality"]["score"] < r["categories"]["construction_quality"]["max"]


def test_evidence_requirement_change_028():
    cats = {
        "technical_compliance": {"score": 40, "evidence": "", "tool": ""},  # no evidence
        "construction_quality": {"score": 45, "evidence": "fine", "tool": "x"},
    }
    r = rubric_scorer.score_automated_with_evidence("rubric_a", {}, cats)
    assert r["rejected"] and not r["passed_gate"]


def test_combined_failure_paths(good_character):
    r = rubric_scorer.score_rubric_a(good_character)
    ok, msg = rubric_scorer.combined_passes(r, 12)
    assert ok
    ok, msg = rubric_scorer.combined_passes(r, 9)  # 94 combined: human-gate rejection
    assert not ok and "adjustment loop" in msg
    failed = dict(r)
    failed["passed_gate"] = False
    ok, msg = rubric_scorer.combined_passes(failed, 15)
    assert not ok and "rebuild" in msg
    with pytest.raises(ValueError):
        rubric_scorer.combined_passes(r, 16)


def test_rubric_b_seams_and_completeness(rng):
    tiles = {f"grass_{i}": make_tile(rng, 16) for i in range(3)}
    from tools.tileset_anchor_extractor import extract_anchor

    anchor = extract_anchor(list(tiles.values()))
    r = rubric_scorer.score_rubric_b(tiles, anchor=anchor, required_types=set(tiles))
    assert r["categories"]["seam_integrity"]["score"] == 30, r["categories"]["seam_integrity"]["evidence"]
    assert r["categories"]["completeness"]["score"] == 10

    r2 = rubric_scorer.score_rubric_b(tiles, anchor=anchor, required_types=set(tiles) | {"grass_to_dirt"})
    assert r2["categories"]["completeness"]["score"] == 0  # missing transition tile


def test_rubric_selection():
    assert rubric_scorer.select_rubric("character") == "A"
    assert rubric_scorer.select_rubric("tileset") == "B"
    assert rubric_scorer.select_rubric("parallax") == "C"
    with pytest.raises(ValueError):
        rubric_scorer.select_rubric("nonsense")


def test_seam_validator_catches_non_tiling(rng, good_tile):
    assert seam_validator.check_self(good_tile).ok  # wrapped-noise tile is seamless
    bad = good_tile.copy()
    bad[:, -2:] = (248, 8, 8, 255)  # hard vertical stripe breaks the wrap
    assert not seam_validator.check_self(bad).ok
