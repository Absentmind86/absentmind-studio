"""dna_extractor + dna_diff: extraction, versioning, self-consistency, drift detection."""

from __future__ import annotations

import numpy as np
import pytest

from tools import dna_diff, dna_extractor
from tools._common import save_rgba


@pytest.fixture()
def workspace(tmp_path, good_character):
    sprite_path = tmp_path / "master.png"
    save_rgba(good_character, sprite_path)
    dna_dir = tmp_path / "dna"
    return sprite_path, dna_dir, good_character


def _extract(sprite_path, dna_dir, cid="test_hero"):
    return dna_extractor.extract(
        sprite_path, character_id=cid, character_name="Test Hero", dna_dir=dna_dir
    )


def test_extract_writes_versioned_json(workspace):
    sprite_path, dna_dir, _ = workspace
    dna = _extract(sprite_path, dna_dir)
    assert dna["version"] == 1
    assert (dna_dir / "test_hero_v1.json").is_file()
    dna2 = _extract(sprite_path, dna_dir)  # re-approval -> v2, v1 retained
    assert dna2["version"] == 2
    assert (dna_dir / "test_hero_v1.json").is_file()
    assert (dna_dir / "test_hero_v2.json").is_file()


def test_master_sprite_matches_own_dna(workspace):
    sprite_path, dna_dir, arr = workspace
    dna = _extract(sprite_path, dna_dir)
    report = dna_diff.diff(dna, arr)
    assert report.ok, report.violations
    assert report.consistency == 1.0


def test_palette_drift_detected(workspace):
    sprite_path, dna_dir, arr = workspace
    dna = _extract(sprite_path, dna_dir)
    drifted = arr.copy()
    vis = drifted[..., 3] >= 128
    ys, xs = np.nonzero(vis)
    for i in range(6):
        drifted[ys[i], xs[i], :3] = (8, 248, 248)  # off-DNA color
    report = dna_diff.diff(dna, drifted)
    assert not report.ok
    assert report.consistency < 1.0
    assert len(report.off_palette_pixels) == 6


def test_verify_entry_point(workspace, tmp_path):
    sprite_path, dna_dir, _ = workspace
    dna = _extract(sprite_path, dna_dir)
    ok, msg = dna_diff.verify_dna_matches_sprite(
        dna_dir / "test_hero_v1.json", sprite_path
    )
    assert ok, msg
