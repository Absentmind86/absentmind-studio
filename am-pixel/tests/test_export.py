"""Exporters: generic JSON, Godot .tres, RPG Maker MZ layout, GameMaker strips."""

from __future__ import annotations

import json

import numpy as np
import pytest

from tools import sheet_manager
from tools._common import load_rgba
from tools.export import gamemaker_exporter, generic_exporter, godot_exporter, rpgmaker_exporter


def _frame(v, w=16, h=24):
    f = np.zeros((h, w, 4), dtype=np.uint8)
    f[..., 1] = v
    f[..., 3] = 255
    return f


@pytest.fixture()
def walk_sheet(tmp_path):
    sheet = sheet_manager.create_sheet(
        "hero", "world", cell_w=16, cell_h=24, cols=3, rows=4,
        png_path=tmp_path / "hero.png", sheets_dir=tmp_path / "sheets",
    )
    for anim, base in (("walk_down", 40), ("walk_left", 80), ("walk_right", 120), ("walk_up", 160)):
        sheet_manager.add_frames(sheet, [_frame(base + i) for i in range(3)], animation=anim)
    return sheet


def test_generic_export(walk_sheet, tmp_path):
    out = generic_exporter.export(walk_sheet.data, walk_sheet.png_path, tmp_path / "out")
    data = json.loads(out.read_text())
    assert set(data["animations"]) == {"walk_down", "walk_left", "walk_right", "walk_up"}
    assert len(data["animations"]["walk_down"]) == 3
    assert (tmp_path / "out" / "hero_world.png").is_file()


def test_godot_export(walk_sheet, tmp_path):
    out = godot_exporter.export(walk_sheet.data, walk_sheet.png_path, tmp_path / "out")
    text = out.read_text()
    assert 'type="SpriteFrames"' in text
    assert text.count("AtlasTexture_") >= 12 * 2  # 12 defs + 12 refs
    assert '&"walk_up"' in text


def test_rpgmaker_export(walk_sheet, tmp_path):
    out = rpgmaker_exporter.export(walk_sheet.data, walk_sheet.png_path, tmp_path / "out")
    assert out.name == "$hero.png"
    png = load_rgba(out)
    assert png.shape == (4 * 24, 3 * 16, 4)
    assert np.all(png[0:24, 0:16, 1] == 40)  # row 0 = walk_down frame 0
    assert np.all(png[72:96, 0:16, 1] == 160)  # row 3 = walk_up frame 0


def test_gamemaker_export(walk_sheet, tmp_path):
    out = gamemaker_exporter.export(walk_sheet.data, walk_sheet.png_path, tmp_path / "out")
    data = json.loads(out.read_text())
    assert data["strips"]["walk_down"]["frames"] == 3
    strip = load_rgba(tmp_path / "out" / data["strips"]["walk_down"]["image"])
    assert strip.shape == (24, 48, 4)
