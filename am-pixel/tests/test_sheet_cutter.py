"""sheet_cutter: grid inference, pixel-exact recovery, anti-bounce alignment.

The core guarantee under test: frames drawn on a shared canvas, then scattered
into sheet cells at random offsets (simulating a sheet whose author centered
each frame by eye), must come back out aligned to the pixel — zero residual
shift between consecutive frames.
"""

from __future__ import annotations

import numpy as np
import pytest

from data.pipeline.sheet_cutter import (
    GridGuess,
    align_frames,
    cut_grid,
    ghost_overlay,
    infer_grid,
    stability_report,
)
from data.pipeline.validation_corpus import make_character
from tools._common import alpha_mask


def _walk_frames(rng, n=4):
    """Feet-planted walk cycle on a shared 16x24 canvas: legs swing, head steady."""
    base = make_character(rng, 16, 24)
    frames = []
    leg_rows = slice(17, 23)  # above the bottom outline row so feet stay planted
    for k in range(n):
        f = base.copy()
        f[leg_rows] = np.roll(f[leg_rows], (k % 2) * 2 - 1, axis=1)  # swing legs ±1
        frames.append(f)
    return frames


def _sheet_from_frames(frames, cell_w=24, cell_h=32, jitter=3, seed=5):
    """Scatter frames into cells at random offsets — the placement error the
    cutter must undo. Returns (sheet, trimmed_reference_frames)."""
    rng = np.random.default_rng(seed)
    sheet = np.zeros((cell_h, cell_w * len(frames), 4), dtype=np.uint8)
    for i, f in enumerate(frames):
        vis = alpha_mask(f)
        ys, xs = np.nonzero(vis)
        t = f[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
        oy = int(rng.integers(0, jitter + 1))
        ox = int(rng.integers(0, jitter + 1))
        sheet[oy : oy + t.shape[0], i * cell_w + ox : i * cell_w + ox + t.shape[1]] = t
    return sheet


@pytest.fixture()
def walk(rng):
    return _walk_frames(rng)


def test_grid_inference_with_gutters(walk):
    sheet = _sheet_from_frames(walk, cell_w=24, cell_h=32)
    g = infer_grid(sheet)
    assert (g.cell_w, g.cell_h) == (24, 32), (g.cell_w, g.cell_h, g.confidence)
    assert g.confidence >= 0.55


def test_grid_inference_prefers_smallest_period(walk):
    # 8 identical-size cells: period 24 must win over 48/72/96
    sheet = _sheet_from_frames(walk + walk, cell_w=24, cell_h=32)
    g = infer_grid(sheet)
    assert g.cell_w == 24


def test_cut_grid_skips_empty_cells(walk):
    sheet = _sheet_from_frames(walk, cell_w=24, cell_h=32)
    wider = np.zeros((32, 24 * 6, 4), dtype=np.uint8)  # two empty trailing cells
    wider[:, : sheet.shape[1]] = sheet
    cells = cut_grid(wider, 24, 32)
    assert len(cells) == 4


def test_alignment_kills_placement_jitter(walk):
    """The signature test: random per-cell offsets in, zero residual shift out."""
    sheet = _sheet_from_frames(walk, cell_w=24, cell_h=32, jitter=3)
    cells = [c for (_, _, c) in cut_grid(sheet, 24, 32)]
    placed = align_frames(cells, mode="baseline")
    rep = stability_report(placed)
    assert rep.stable, rep.summary()
    # and the recovered frames are pixel-identical to the shared-canvas originals
    # up to a single global (dy, dx): compare pairwise silhouette deltas instead
    for orig_a, orig_b, got_a, got_b in zip(walk, walk[1:], placed, placed[1:]):
        want = int(np.count_nonzero(alpha_mask(orig_a) ^ alpha_mask(orig_b)))
        have = int(np.count_nonzero(alpha_mask(got_a) ^ alpha_mask(got_b)))
        assert want == have, "relative frame geometry changed during cut+align"


def test_unaligned_frames_detected(walk):
    """Naive bbox-centering (what the cutter prevents) must be flagged unstable."""
    sheet = _sheet_from_frames(walk, cell_w=24, cell_h=32, jitter=3)
    cells = [c for (_, _, c) in cut_grid(sheet, 24, 32)]
    rep = stability_report(cells)  # raw cells still carry the random offsets
    assert not rep.stable
    assert rep.max_residual >= 1


def test_ghost_overlay_written(tmp_path, walk):
    placed = align_frames(walk, mode="baseline")
    out = tmp_path / "ghost.png"
    ghost_overlay(placed, out)
    assert out.is_file()


def test_correlate_xy_mode(walk):
    placed = align_frames(walk, mode="correlate-xy")
    assert stability_report(placed).stable
