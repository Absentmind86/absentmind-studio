"""
Non-destructive sprite sheet management (SPEC §5.2).

Each sheet has a JSON layout manifest (sheets/[character_id]_[profile].json).
Occupied cells are locked: add_frames() writes ONLY into empty cells and
raises rather than touching an occupied cell's pixels. When the sheet is
full it is expanded by whole rows. Frame records support
"status": "superseded_by_rollback_v2" (CHANGE-029) — PNGs stay in git,
manifests mark frames non-authoritative.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import load_rgba, save_rgba  # noqa: E402

SHEETS_DIR = _AM_PIXEL / "sheets"


@dataclass
class Sheet:
    manifest_path: Path
    data: dict

    @property
    def png_path(self) -> Path:
        return Path(self.data["png_path"])

    def cell_box(self, row: int, col: int) -> tuple[int, int, int, int]:
        cw, ch = self.data["cell_w"], self.data["cell_h"]
        return row * ch, col * cw, (row + 1) * ch, (col + 1) * cw

    def occupied(self) -> set[tuple[int, int]]:
        return {
            (f["row"], f["col"])
            for f in self.data["frames"]
            if not f.get("status", "active").startswith("superseded")
        }

    def all_cells(self) -> set[tuple[int, int]]:
        return {(r, c) for r in range(self.data["rows"]) for c in range(self.data["cols"])}

    def empty_cells(self) -> list[tuple[int, int]]:
        used = {(f["row"], f["col"]) for f in self.data["frames"]}  # superseded cells stay reserved
        return sorted(self.all_cells() - used)

    def save(self) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def create_sheet(
    character_id: str,
    profile: str,
    *,
    cell_w: int,
    cell_h: int,
    cols: int = 4,
    rows: int = 4,
    png_path: Path | str | None = None,
    sheets_dir: Path | None = None,
    dna_version: int = 1,
) -> Sheet:
    sheets_dir = sheets_dir or SHEETS_DIR
    manifest_path = sheets_dir / f"{character_id}_{profile}.json"
    if manifest_path.exists():
        raise FileExistsError(f"sheet manifest already exists: {manifest_path}")
    png = Path(png_path) if png_path else _AM_PIXEL / "assets" / "characters" / character_id / f"{profile}.png"
    sheet = Sheet(
        manifest_path,
        {
            "character_id": character_id,
            "profile": profile,
            "cell_w": cell_w,
            "cell_h": cell_h,
            "cols": cols,
            "rows": rows,
            "png_path": str(png),
            "dna_version": dna_version,
            "frames": [],
        },
    )
    png.parent.mkdir(parents=True, exist_ok=True)
    save_rgba(np.zeros((rows * cell_h, cols * cell_w, 4), dtype=np.uint8), png)
    sheet.save()
    return sheet


def load_sheet(character_id: str, profile: str, sheets_dir: Path | None = None) -> Sheet:
    manifest_path = (sheets_dir or SHEETS_DIR) / f"{character_id}_{profile}.json"
    return Sheet(manifest_path, json.loads(manifest_path.read_text(encoding="utf-8")))


def expand_sheet(sheet: Sheet, extra_rows: int = 2) -> None:
    """Grow the sheet downward — existing pixels are never moved or altered."""
    png = load_rgba(sheet.png_path)
    ch, cw = sheet.data["cell_h"], sheet.data["cell_w"]
    new = np.zeros((png.shape[0] + extra_rows * ch, png.shape[1], 4), dtype=np.uint8)
    new[: png.shape[0]] = png
    save_rgba(new, sheet.png_path)
    sheet.data["rows"] += extra_rows
    sheet.save()


def add_frames(
    sheet: Sheet,
    frames: list[np.ndarray],
    *,
    animation: str,
    dna_version: int | None = None,
) -> list[dict]:
    """Place frames into empty cells only (non-destructive guarantee).
    Expands the sheet if needed. Returns the new frame records."""
    ch, cw = sheet.data["cell_h"], sheet.data["cell_w"]
    for i, f in enumerate(frames):
        if f.shape[0] != ch or f.shape[1] != cw:
            raise ValueError(f"frame {i} is {f.shape[1]}x{f.shape[0]}, sheet cells are {cw}x{ch}")

    while len(sheet.empty_cells()) < len(frames):
        expand_sheet(sheet)

    png = load_rgba(sheet.png_path)
    occupied_boxes = [sheet.cell_box(r, c) for (r, c) in sheet.occupied()]
    before = png.copy()

    records = []
    cells = sheet.empty_cells()[: len(frames)]
    for i, ((row, col), frame) in enumerate(zip(cells, frames)):
        y0, x0, y1, x1 = sheet.cell_box(row, col)
        png[y0:y1, x0:x1] = frame
        records.append(
            {
                "row": row,
                "col": col,
                "animation": animation,
                "frame_index": i,
                "status": "active",
                "dna_version": dna_version or sheet.data.get("dna_version", 1),
            }
        )

    for (y0, x0, y1, x1) in occupied_boxes:  # verify the guarantee, don't just intend it
        if not np.array_equal(before[y0:y1, x0:x1], png[y0:y1, x0:x1]):
            raise RuntimeError("non-destructive guarantee violated — occupied cell modified; aborting write")

    save_rgba(png, sheet.png_path)
    sheet.data["frames"].extend(records)
    sheet.save()
    return records


def mark_superseded(sheet: Sheet, dna_version_to: int) -> int:
    """DNA rollback support (CHANGE-029): flag active frames as superseded."""
    n = 0
    for f in sheet.data["frames"]:
        if f.get("status", "active") == "active":
            f["status"] = f"superseded_by_rollback_v{dna_version_to}"
            n += 1
    sheet.save()
    return n


def get_frame(sheet: Sheet, row: int, col: int) -> np.ndarray:
    png = load_rgba(sheet.png_path)
    y0, x0, y1, x1 = sheet.cell_box(row, col)
    return png[y0:y1, x0:x1].copy()


def main() -> None:
    raise SystemExit("library module — use create_sheet/load_sheet/add_frames from pipeline code")


if __name__ == "__main__":
    main()
