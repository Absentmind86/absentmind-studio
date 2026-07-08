"""
Pixel-perfect sprite sheet cutting (Phase 3 ingestion tooling).

The two failure modes this tool exists to prevent:

1. WRONG GRID — cutting on the wrong cell size/offset slices through sprites.
   infer_grid() scores every candidate cell size by (a) gutter emptiness at
   the implied cut lines and (b) silhouette autocorrelation at that period
   (sprites in adjacent cells of the same sheet overlap heavily when the
   sheet is shifted by exactly one cell). The smallest period within epsilon
   of the best score wins (a true 16px grid also scores high at 32px — the
   smaller period is the real one). Low confidence is REPORTED, never
   silently guessed past — the CLI refuses to cut below the confidence
   floor unless --force.

2. ANIMATION BOUNCE — trimming frames to their bounding boxes destroys their
   shared anchor: a frame whose raised arm extends its bbox 2px left will
   jump 2px right when re-canvased. align_frames() re-anchors every frame on
   a common canvas: the silhouette BASELINE (bottom row — feet) is pinned,
   and horizontal placement is recovered by integer cross-correlation of
   consecutive silhouettes (the shift that maximizes overlap). Residual
   jitter is then MEASURED, not assumed: stability_report() recomputes the
   optimal shift between every consecutive placed pair — (0,0) everywhere
   means pixel-stable. A ghost-overlay PNG is written so a human can verify
   by eye.

   Known ambiguity (documented, not hidden): a genuine vertical head-bob is
   indistinguishable from vertical placement error without semantics.
   Baseline mode assumes feet-planted animations (walk cycles — the common
   case). For flying/jumping rows use --align correlate-xy and review the
   ghost overlay.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools._common import alpha_mask, load_rgba, save_rgba  # noqa: E402

CONFIDENCE_FLOOR = 0.55


# ------------------------------------------------------------------ grid inference


@dataclass
class GridGuess:
    cell_w: int
    cell_h: int
    offset_x: int
    offset_y: int
    confidence: float  # 0..1
    runner_up: tuple[int, int] | None = None


def _bands(occ: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous runs of occupied columns/rows -> [(start, end_exclusive)]."""
    out, start = [], None
    for i, v in enumerate(occ):
        if v > 0 and start is None:
            start = i
        elif v == 0 and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(occ)))
    return out


def _empty_line_score(occ: np.ndarray, cell: int, offset: int) -> tuple[float, int]:
    """Fraction of interior cut lines that no sprite CROSSES, and line count.
    A cut at x splits columns x-1 | x; content may touch the line from either
    side (a sprite starting exactly on a cell boundary is legal) — the line is
    dirty only when both sides are occupied, i.e. a sprite straddles it. At
    the true (cell, offset) of a guttered sheet this is 1.0; a wrong period
    drifts across the sheet and slices sprites."""
    length = len(occ)
    lines = [offset + k * cell for k in range(1, (length - offset) // cell + 1)]
    lines = [l for l in lines if 0 < l < length]
    if not lines:
        return 0.0, 0
    clean = sum(1 for l in lines if not (occ[l] > 0 and occ[l - 1] > 0))
    return clean / len(lines), len(lines)


def _autocorr_score(vis: np.ndarray, c: int, axis: int) -> float:
    if axis == 1:
        a, b = vis[:, :-c], vis[:, c:]
    else:
        a, b = vis[:-c, :], vis[c:, :]
    inter = np.count_nonzero(a & b)
    union = np.count_nonzero(a | b)
    return inter / union if union else 0.0


def _axis_infer(vis: np.ndarray, axis: int, min_cell: int, max_cell: int) -> tuple[int, int, float]:
    """-> (cell, offset, confidence) for one axis (axis=1 -> widths)."""
    occ = vis.sum(axis=0 if axis == 1 else 1).astype(float)
    length = vis.shape[1] if axis == 1 else vis.shape[0]
    bands = _bands(occ)

    if len(bands) <= 1:
        # single band: one cell spans the whole axis (single-row/column sheet)
        return length, 0, 0.9 if bands else 0.0

    # primary: period from band spacing (robust to per-cell content jitter),
    # refined over nearby candidates + offsets by exact-empty-line score
    starts = np.array([s for s, _ in bands])
    est = int(round(float(np.median(np.diff(starts))))) if len(starts) > 1 else length
    # rank: empty-line score, then exact-multiple-with-zero-offset (sheets are
    # authored as whole multiples of the cell — several jitter-tolerant cuts
    # can be "clean", but the authored grid divides the sheet), then cell size
    best = (0.0, 0, 0, est, 0)  # (score, divides, -distance_to_est, c, off)
    for c in range(max(min_cell, est - 3), min(max_cell, est + 3, length) + 1):
        for off in range(0, min(c, bands[0][0] + 1)):
            score, n_lines = _empty_line_score(occ, c, off)
            if not n_lines:
                continue
            divides = 1 if (off == 0 and length % c == 0) else 0
            key = (score, divides, -abs(c - est), c, off)
            if key[:3] > best[:3]:
                best = key
    if best[0] >= 0.99:  # every cut line empty — unambiguous gutter grid
        return best[3], best[4], round(0.7 + 0.3 * best[0], 3)

    # fallback: silhouette autocorrelation with divisor preference (a true
    # period's multiples also score high; prefer the smallest DIVISOR of the
    # argmax that stays within epsilon — never an arbitrary nearby size)
    scores = {
        c: _autocorr_score(vis, c, axis)
        for c in range(min_cell, min(max_cell, length // 2) + 1)
    }
    if not scores:
        return length, 0, 0.0
    top = max(scores, key=scores.get)
    chosen = top
    for d in range(min_cell, top):
        if top % d == 0 and scores.get(d, 0.0) >= scores[top] - 0.04:
            chosen = d
            break
    return chosen, 0, round(scores[chosen], 3)


def infer_grid(sheet: np.ndarray, *, min_cell: int = 8, max_cell: int = 160) -> GridGuess:
    vis = alpha_mask(sheet)
    if not vis.any():
        return GridGuess(0, 0, 0, 0, 0.0)
    cw, ox, conf_w = _axis_infer(vis, 1, min_cell, max_cell)
    ch, oy, conf_h = _axis_infer(vis, 0, min_cell, max_cell)
    return GridGuess(
        cell_w=cw, cell_h=ch, offset_x=ox, offset_y=oy,
        confidence=round(min(conf_w, conf_h), 3),
    )


def cut_grid(
    sheet: np.ndarray, cell_w: int, cell_h: int, offset_x: int = 0, offset_y: int = 0
) -> list[tuple[int, int, np.ndarray]]:
    """-> [(row, col, cell_rgba)] for non-empty cells, raster order."""
    h, w = sheet.shape[:2]
    out = []
    row = 0
    for y0 in range(offset_y, h - cell_h + 1, cell_h):
        col = 0
        for x0 in range(offset_x, w - cell_w + 1, cell_w):
            cell = sheet[y0 : y0 + cell_h, x0 : x0 + cell_w]
            if alpha_mask(cell).any():
                out.append((row, col, cell.copy()))
            col += 1
        row += 1
    return out


# ------------------------------------------------------------------ alignment


def _trim(frame: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
    vis = alpha_mask(frame)
    ys, xs = np.nonzero(vis)
    if len(ys) == 0:
        return frame, (0, 0)
    return frame[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1].copy(), (int(ys.min()), int(xs.min()))


def _best_shift(a_vis: np.ndarray, b_vis: np.ndarray, max_shift: int = 6, dy_fixed: int | None = None) -> tuple[int, int]:
    """Integer (dy, dx) applied to b that maximizes silhouette overlap with a."""
    best, best_shift = -1, (0, 0)
    dys = [dy_fixed] if dy_fixed is not None else range(-max_shift, max_shift + 1)
    for dy in dys:
        rolled_y = np.roll(b_vis, dy, axis=0)
        for dx in range(-max_shift, max_shift + 1):
            rolled = np.roll(rolled_y, dx, axis=1)
            inter = int(np.count_nonzero(a_vis & rolled))
            if inter > best or (inter == best and abs(dx) + abs(dy) < abs(best_shift[1]) + abs(best_shift[0])):
                best, best_shift = inter, (dy, dx)
    return best_shift


def align_frames(
    frames: list[np.ndarray],
    *,
    canvas: tuple[int, int] | None = None,
    mode: str = "baseline",  # "baseline" (feet-planted) | "correlate-xy"
    margin: int = 2,
) -> list[np.ndarray]:
    """Place trimmed frames on a common canvas with a stable shared anchor.

    baseline:      silhouette bottom row pinned at a fixed canvas row for ALL
                   frames; horizontal position chained by cross-correlation.
    correlate-xy:  both axes chained by cross-correlation (for animations
                   with no planted baseline).
    """
    trimmed = [_trim(f)[0] for f in frames]
    max_h = max(t.shape[0] for t in trimmed)
    max_w = max(t.shape[1] for t in trimmed)
    cw, ch = canvas if canvas else (max_w + 2 * margin, max_h + 2 * margin)
    if max_w > cw or max_h > ch:
        raise ValueError(f"canvas {cw}x{ch} smaller than largest frame {max_w}x{max_h}")

    placed: list[np.ndarray] = []
    baseline_row = ch - 1 - margin
    prev_vis = None
    prev_x = None
    for t in trimmed:
        th, tw = t.shape[:2]
        y0 = (baseline_row - th + 1) if mode == "baseline" else (ch - th) // 2
        x0 = (cw - tw) // 2
        cell = np.zeros((ch, cw, 4), dtype=np.uint8)
        cell[y0 : y0 + th, x0 : x0 + tw] = t
        vis = alpha_mask(cell)
        if prev_vis is not None:
            dy, dx = _best_shift(prev_vis, vis, dy_fixed=0 if mode == "baseline" else None)
            if dy or dx:
                cell = np.roll(np.roll(cell, dy, axis=0), dx, axis=1)
                vis = alpha_mask(cell)
                # refuse wrap-around: content must not cross canvas edges
                if vis[:, 0].any() and vis[:, -1].any():
                    raise ValueError("frame content wrapped during alignment — use a larger canvas")
        placed.append(cell)
        prev_vis, prev_x = vis, x0
    return placed


@dataclass
class StabilityReport:
    stable: bool
    residual_shifts: list[tuple[int, int]] = field(default_factory=list)  # per consecutive pair
    max_residual: int = 0

    def summary(self) -> str:
        if self.stable:
            return f"pixel-stable — residual shift (0,0) across all {len(self.residual_shifts)} frame pairs"
        return f"UNSTABLE — residual shifts {self.residual_shifts} (animation will bounce)"


def stability_report(placed: list[np.ndarray]) -> StabilityReport:
    shifts = []
    for a, b in zip(placed, placed[1:]):
        dy, dx = _best_shift(alpha_mask(a), alpha_mask(b))
        shifts.append((dy, dx))
    max_r = max((abs(dy) + abs(dx) for dy, dx in shifts), default=0)
    return StabilityReport(stable=max_r == 0, residual_shifts=shifts, max_residual=max_r)


def ghost_overlay(placed: list[np.ndarray], out_path: Path | str, scale: int = 4) -> None:
    """All frames superimposed at reduced opacity — bounce is instantly visible
    to a human as edge smearing; a stable cycle reads as one crisp figure with
    only the moving limbs ghosted."""
    ch, cw = placed[0].shape[:2]
    acc = np.zeros((ch, cw, 3), dtype=np.float32)
    hits = np.zeros((ch, cw), dtype=np.float32)
    for f in placed:
        m = alpha_mask(f)
        acc[m] += f[m, :3].astype(np.float32)
        hits += m
    out = np.zeros((ch, cw, 4), dtype=np.uint8)
    nz = hits > 0
    out[nz, :3] = (acc[nz] / hits[nz, None]).astype(np.uint8)
    out[nz, 3] = np.clip(80 + 175 * hits[nz] / len(placed), 0, 255).astype(np.uint8)
    big = np.kron(out, np.ones((scale, scale, 1), dtype=np.uint8))
    save_rgba(big, out_path)


# ------------------------------------------------------------------ CLI


def cut_sheet_file(
    src: Path | str,
    out_dir: Path | str,
    *,
    grid: tuple[int, int, int, int] | None = None,
    align: str = "baseline",
    canvas: tuple[int, int] | None = None,
    force: bool = False,
) -> dict:
    sheet = load_rgba(src)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(src).stem

    if grid is None:
        guess = infer_grid(sheet)
        if guess.confidence < CONFIDENCE_FLOOR and not force:
            raise SystemExit(
                f"grid inference confidence {guess.confidence} below floor {CONFIDENCE_FLOOR} "
                f"(best guess {guess.cell_w}x{guess.cell_h}+{guess.offset_x}+{guess.offset_y}, "
                f"runner-up {guess.runner_up}) — pass --grid WxH+OX+OY explicitly or --force"
            )
        grid = (guess.cell_w, guess.cell_h, guess.offset_x, guess.offset_y)
        print(f"inferred grid {grid[0]}x{grid[1]} offset +{grid[2]}+{grid[3]} (confidence {guess.confidence})")

    cells = cut_grid(sheet, *grid)
    rows: dict[int, list[np.ndarray]] = {}
    for row, col, cell in cells:
        rows.setdefault(row, []).append(cell)

    report: dict = {"source": str(src), "grid": grid, "rows": {}}
    for row, frames in sorted(rows.items()):
        placed = align_frames(frames, mode=align, canvas=canvas)
        stab = stability_report(placed)
        for i, f in enumerate(placed):
            save_rgba(f, out_dir / f"{stem}_r{row}_f{i}.png")
        ghost_overlay(placed, out_dir / f"{stem}_r{row}_ghost.png")
        report["rows"][row] = {
            "frames": len(placed),
            "stable": stab.stable,
            "residual_shifts": stab.residual_shifts,
        }
        flag = "OK" if stab.stable else "REVIEW GHOST OVERLAY"
        print(f"row {row}: {len(placed)} frames — {stab.summary()} [{flag}]")

    (out_dir / f"{stem}_cut_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Pixel-perfect sprite sheet cutter")
    p.add_argument("sheet")
    p.add_argument("out_dir")
    p.add_argument("--grid", help="WxH+OX+OY, e.g. 32x32+0+0 (omit to infer)")
    p.add_argument("--align", choices=["baseline", "correlate-xy"], default="baseline")
    p.add_argument("--canvas", help="output canvas WxH (default: max frame + margin)")
    p.add_argument("--force", action="store_true", help="cut even below the confidence floor")
    args = p.parse_args()

    grid = None
    if args.grid:
        wh, ox, oy = args.grid.split("+")
        w, h = wh.lower().split("x")
        grid = (int(w), int(h), int(ox), int(oy))
    canvas = None
    if args.canvas:
        w, h = args.canvas.lower().split("x")
        canvas = (int(w), int(h))
    cut_sheet_file(args.sheet, args.out_dir, grid=grid, align=args.align, canvas=canvas, force=args.force)


if __name__ == "__main__":
    main()
