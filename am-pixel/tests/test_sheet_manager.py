"""sheet_manager: non-destructive guarantee, expansion, rollback flags."""

from __future__ import annotations

import numpy as np
import pytest

from tools import sheet_manager
from tools._common import load_rgba


def _frame(value: int, w=16, h=24) -> np.ndarray:
    f = np.zeros((h, w, 4), dtype=np.uint8)
    f[..., 0] = value
    f[..., 3] = 255
    return f


@pytest.fixture()
def sheet(tmp_path):
    return sheet_manager.create_sheet(
        "hero", "world", cell_w=16, cell_h=24, cols=2, rows=2,
        png_path=tmp_path / "hero_world.png", sheets_dir=tmp_path / "sheets",
    )


def test_add_frames_fills_empty_cells(sheet):
    recs = sheet_manager.add_frames(sheet, [_frame(40), _frame(80)], animation="walk_down")
    assert [(r["row"], r["col"]) for r in recs] == [(0, 0), (0, 1)]
    assert np.all(sheet_manager.get_frame(sheet, 0, 0)[..., 0] == 40)


def test_existing_pixels_never_modified(sheet):
    sheet_manager.add_frames(sheet, [_frame(40)], animation="walk_down")
    before = sheet_manager.get_frame(sheet, 0, 0).copy()
    sheet_manager.add_frames(sheet, [_frame(200), _frame(220), _frame(240)], animation="walk_up")
    assert np.array_equal(sheet_manager.get_frame(sheet, 0, 0), before)


def test_sheet_expands_when_full(sheet):
    sheet_manager.add_frames(sheet, [_frame(v) for v in (10, 20, 30, 40)], animation="walk_down")
    assert sheet.data["rows"] == 2
    sheet_manager.add_frames(sheet, [_frame(50)], animation="surprise")
    assert sheet.data["rows"] == 4  # expanded
    png = load_rgba(sheet.png_path)
    assert png.shape[0] == 4 * 24
    assert np.all(sheet_manager.get_frame(sheet, 0, 0)[..., 0] == 10)  # originals intact


def test_wrong_frame_size_rejected(sheet):
    with pytest.raises(ValueError):
        sheet_manager.add_frames(sheet, [_frame(10, w=8, h=8)], animation="walk_down")


def test_rollback_marks_superseded_and_reserves_cells(sheet):
    sheet_manager.add_frames(sheet, [_frame(10), _frame(20)], animation="walk_down")
    n = sheet_manager.mark_superseded(sheet, dna_version_to=2)
    assert n == 2
    assert all(f["status"] == "superseded_by_rollback_v2" for f in sheet.data["frames"])
    # superseded cells stay reserved — new frames go elsewhere, PNGs preserved
    recs = sheet_manager.add_frames(sheet, [_frame(99)], animation="walk_down_v2")
    assert (recs[0]["row"], recs[0]["col"]) not in {(0, 0), (0, 1)}
