"""
Rubric A/B/C scoring (SPEC §8.3, CHANGE-013/028/033).

Tier 1 automated gate = 85 hard points. The gate is all-or-nothing per
category at the pass/fail level (85/85 required), but category scores are
proportional for diagnostics — a failing sprite's report says how far off
it was and exactly which tool flagged what (CHANGE-028: scores >= 70 carry
structured evidence or are rejected).

Tier 2 human gate = 15 points, awarded in the approval UI (Originality 10,
Soul/Visual Hierarchy 5 for Rubric A). combined_passes() applies the two
failure paths from §8.2 (CHANGE-035).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, TypedDict

import numpy as np

_AM_PIXEL = Path(__file__).resolve().parent.parent
if str(_AM_PIXEL) not in sys.path:
    sys.path.insert(0, str(_AM_PIXEL))

from tools import (  # noqa: E402
    anti_aliasing_detector,
    banding_detector,
    outline_checker,
    palette_validator,
)
from tools._common import alpha_mask  # noqa: E402

AUTOMATED_MAX = 85
HUMAN_MAX = 15
COMBINED_PASS = 95


class CategoryEvidence(TypedDict, total=False):
    score: int
    max: int
    tool: str
    tools: list[str]
    evidence: str


class AutomatedScoreResult(TypedDict, total=False):
    automated_score: int
    passed_gate: bool
    evidence_complete: bool
    categories: dict[str, CategoryEvidence]
    rejected: bool
    rejection_reason: str


# --------------------------------------------------------------------------- Rubric A


def _readability(rgba: np.ndarray) -> tuple[float, str]:
    """Silhouette readability heuristic: enough visible mass to read at 1x,
    and a coherent (not speckled) silhouette — single dominant component."""
    vis = alpha_mask(rgba)
    total = vis.size
    mass = np.count_nonzero(vis) / total
    if mass < 0.15:
        return 0.0, f"visible mass {mass:.0%} too sparse to read at 1x"
    from tools._common import connected_region_sizes

    solid = (vis.astype(np.int16))
    sizes = connected_region_sizes(np.where(vis, 1, 0).astype(np.int16))
    largest = sizes.max() if sizes.size else 0
    coherence = largest / max(np.count_nonzero(vis), 1)
    if coherence < 0.85:
        return 0.5, f"silhouette fragmented — largest component {coherence:.0%} of visible pixels"
    return 1.0, f"mass {mass:.0%}, silhouette coherence {coherence:.0%}"


def _pose_consistency(frames: list[np.ndarray]) -> tuple[float, str]:
    """Walk-cycle pose check: consecutive frames must be similar (same character)
    but not identical (actual motion). Silhouette IoU in (0.55, 0.98)."""
    if len(frames) < 2:
        return 1.0, "single frame — pose consistency not applicable"
    ious = []
    for a, b in zip(frames, frames[1:]):
        ma, mb = alpha_mask(a), alpha_mask(b)
        if ma.shape != mb.shape:
            return 0.0, "frames differ in canvas size"
        inter, union = np.count_nonzero(ma & mb), np.count_nonzero(ma | mb)
        ious.append(inter / union if union else 0.0)
    lo, hi = min(ious), max(ious)
    if lo < 0.55:
        return 0.0, f"adjacent frames IoU {lo:.2f} — reads as different characters"
    if hi > 0.995:
        return 0.5, f"adjacent frames IoU {hi:.3f} — duplicated frames, no motion"
    return 1.0, f"adjacent-frame silhouette IoU {lo:.2f}..{hi:.2f}"


def score_rubric_a(
    rgba: np.ndarray,
    *,
    dna: dict | None = None,
    frames: list[np.ndarray] | None = None,
    is_effect: bool = False,
    effect_category: str = "elemental",
) -> AutomatedScoreResult:
    """Rubric A automated gate. Weights: Technical 25, Construction 25,
    Readability 20, Animation 15 (effects variant: Animation 25, Construction 15)."""
    w_tech, w_con, w_read, w_anim = (25, 15, 20, 25) if is_effect else (25, 25, 20, 15)
    cats: dict[str, CategoryEvidence] = {}

    allowed = None
    if dna is not None:
        from tools.dna_extractor import dna_palette_rgb

        allowed = dna_palette_rgb(dna)
    pr = palette_validator.validate(rgba, allowed)
    aa = anti_aliasing_detector.check(rgba)
    tech = w_tech if (pr.ok and aa.ok) else 0
    cats["technical_compliance"] = {
        "score": tech, "max": w_tech,
        "tools": ["palette_validator", "anti_aliasing_detector"],
        "evidence": f"{pr.summary()}; {aa.summary()}",
    }

    br = banding_detector.check(rgba)
    oc = outline_checker.check(rgba)
    parts = [br.ok, oc.ok]
    dna_note = ""
    if dna is not None:
        from tools.dna_diff import diff as dna_diff_fn

        dr = dna_diff_fn(dna, rgba)
        parts.append(dr.ok)
        dna_note = f"; dna_diff consistency {dr.consistency:.2f}"
    con = round(w_con * sum(parts) / len(parts))
    cats["construction_quality"] = {
        "score": con, "max": w_con,
        "tools": ["banding_detector", "outline_checker"] + (["dna_diff"] if dna else []),
        "evidence": f"{br.summary()}; {oc.summary()}{dna_note}",
    }

    rd_frac, rd_note = _readability(rgba)
    cats["readability"] = {
        "score": round(w_read * rd_frac), "max": w_read,
        "tool": "rubric_scorer._readability",
        "evidence": rd_note,
    }

    if is_effect and frames:
        from tools.effect_timing_evaluator import evaluate as effect_eval

        er = effect_eval(frames, category=effect_category)
        an_frac, an_note = (1.0, "timing/weight conventions met") if er.ok else (0.0, "; ".join(er.problems))
        an_tool = "effect_timing_evaluator"
    else:
        an_frac, an_note = _pose_consistency(frames or [rgba])
        an_tool = "rubric_scorer._pose_consistency"
    cats["animation_quality"] = {
        "score": round(w_anim * an_frac), "max": w_anim,
        "tool": an_tool, "evidence": an_note,
    }

    return score_automated_with_evidence("rubric_a", {}, cats)


# --------------------------------------------------------------------------- Rubric B


def score_rubric_b(
    tiles: dict[str, np.ndarray],
    *,
    anchor: Any | None = None,
    required_types: set[str] | None = None,
    character_sprites: list[np.ndarray] | None = None,
) -> AutomatedScoreResult:
    """Tileset automated gate (CHANGE-033): Seam 30, Texture 20, Visual
    Recession 20, Completeness 10, Technical 5. Human: Atmospheric 15."""
    from tools.seam_validator import check_self
    from tools.tileset_anchor_extractor import _detail_density, check_against_anchor

    cats: dict[str, CategoryEvidence] = {}

    seam_fails = [n for n, t in tiles.items() if not check_self(t).ok]
    cats["seam_integrity"] = {
        "score": 30 if not seam_fails else 0, "max": 30, "tool": "seam_validator",
        "evidence": "all tiles self-seamless" if not seam_fails else f"seam failures: {', '.join(seam_fails)}",
    }

    if anchor is not None:
        tex_fails = {n: p for n, t in tiles.items() if not (r := check_against_anchor(t, anchor))[0] for p in [r[1]]}
        cats["texture_coherence"] = {
            "score": 20 if not tex_fails else 0, "max": 20, "tool": "tileset_anchor_extractor",
            "evidence": "all tiles match Tileset Anchor" if not tex_fails else f"anchor mismatches: {list(tex_fails)}",
        }
    else:
        cats["texture_coherence"] = {"score": 0, "max": 20, "tool": "tileset_anchor_extractor",
                                     "evidence": "no Tileset Anchor provided — cannot score"}

    if character_sprites:
        tile_density = float(np.mean([_detail_density(t) for t in tiles.values()]))
        char_density = float(np.mean([_detail_density(c) for c in character_sprites]))
        recede = tile_density <= char_density * 1.1
        cats["visual_recession"] = {
            "score": 20 if recede else 0, "max": 20, "tool": "tileset_anchor_extractor._detail_density",
            "evidence": f"tile detail {tile_density:.3f} vs character {char_density:.3f} — "
                        + ("recedes correctly" if recede else "tiles compete with characters"),
        }
    else:
        cats["visual_recession"] = {"score": 20, "max": 20, "tool": "tileset_anchor_extractor._detail_density",
                                    "evidence": "no character sprites in project yet — recession vacuously satisfied"}

    missing = sorted((required_types or set()) - set(tiles))
    cats["completeness"] = {
        "score": 10 if not missing else 0, "max": 10, "tool": "rubric_scorer",
        "evidence": "all required tile types present" if not missing else f"missing tile types: {', '.join(missing)}",
    }

    tech_fails = [n for n, t in tiles.items() if not palette_validator.validate(t).ok]
    cats["technical_compliance"] = {
        "score": 5 if not tech_fails else 0, "max": 5, "tool": "palette_validator",
        "evidence": "SNES-legal" if not tech_fails else f"violations in: {', '.join(tech_fails)}",
    }
    return score_automated_with_evidence("rubric_b", {}, cats)


# --------------------------------------------------------------------------- Rubric C


def score_rubric_c(
    layers: list[np.ndarray],
    *,
    character: np.ndarray | None = None,
) -> AutomatedScoreResult:
    """Parallax automated gate (CHANGE-033): Seaming 25, Depth 25, Character
    Contrast 15, Atmospheric (measurable) 15, Technical 5. Human: Tone 10 + feel 5."""
    from tools.layer_compositor import evaluate as parallax_eval
    from tools._common import unique_colors, _hue_sat_val

    rep = parallax_eval(layers, character=character)
    cats: dict[str, CategoryEvidence] = {}

    seam_ok = all(r <= 1.8 for r in rep.layer_seam_ratios)
    cats["layer_seaming"] = {
        "score": 25 if seam_ok else 0, "max": 25, "tool": "layer_compositor",
        "evidence": f"wrap seam ratios {rep.layer_seam_ratios}",
    }
    cats["layer_depth_differentiation"] = {
        "score": 25 if rep.depth_monotonic else 0, "max": 25, "tool": "layer_compositor",
        "evidence": f"detail by layer {rep.detail_by_layer}" + ("" if rep.depth_monotonic else " — depth inverted"),
    }
    if character is not None:
        ok = rep.character_contrast is not None and rep.character_contrast >= 40.0
        cats["character_contrast"] = {
            "score": 15 if ok else 0, "max": 15, "tool": "layer_compositor",
            "evidence": f"contrast {rep.character_contrast}",
        }
    else:
        cats["character_contrast"] = {"score": 15, "max": 15, "tool": "layer_compositor",
                                      "evidence": "no character supplied — vacuously satisfied"}

    # measurable atmospheric consistency: layers share value direction (light) and palette feel
    vals = [float(np.mean([_hue_sat_val(c)[2] for c in unique_colors(l)] or [0])) for l in layers]
    spread = max(vals) - min(vals) if vals else 0.0
    atmos_ok = spread <= 0.45
    cats["atmospheric_measurable"] = {
        "score": 15 if atmos_ok else 0, "max": 15, "tool": "rubric_scorer",
        "evidence": f"layer mean-value spread {spread:.2f} (<=0.45 reads as one scene)",
    }

    tech_fails = [i for i, l in enumerate(layers) if not palette_validator.validate(l).ok]
    cats["technical_compliance"] = {
        "score": 5 if not tech_fails else 0, "max": 5, "tool": "palette_validator",
        "evidence": "SNES-legal" if not tech_fails else f"violations in layers {tech_fails}",
    }
    return score_automated_with_evidence("rubric_c", {}, cats)


# --------------------------------------------------------------------------- shared


def score_automated_with_evidence(
    asset_type: str,
    sprite_meta: dict[str, Any],
    category_results: dict[str, CategoryEvidence],
) -> AutomatedScoreResult:
    """CHANGE-028 Mechanism 2: scores >= 70 must carry per-category evidence."""
    total = sum(c.get("score", 0) for c in category_results.values())
    evidence_complete = all(
        bool(c.get("evidence")) and (bool(c.get("tool")) or bool(c.get("tools")))
        for c in category_results.values()
    )
    out: AutomatedScoreResult = {
        "automated_score": total,
        "passed_gate": total >= AUTOMATED_MAX,
        "evidence_complete": evidence_complete,
        "categories": category_results,
    }
    if total >= 70 and not evidence_complete:
        out["rejected"] = True
        out["passed_gate"] = False
        out["rejection_reason"] = "Score >= 70 requires structured evidence per category (CHANGE-028)."
    return out


def combined_passes(automated: AutomatedScoreResult, human_points: int) -> tuple[bool, str]:
    """The two failure paths of SPEC §8.2 (CHANGE-035)."""
    if not automated.get("passed_gate"):
        return False, "automated gate failed — full rebuild from silhouette (Constitution Rule 4)"
    if not 0 <= human_points <= HUMAN_MAX:
        raise ValueError(f"human points must be 0..{HUMAN_MAX}")
    total = automated["automated_score"] + human_points
    if total >= COMBINED_PASS:
        return True, f"combined {total}/100 — approved"
    return False, (
        f"combined {total}/100 below {COMBINED_PASS} — human-gate rejection; "
        "regenerate via adjustment loop with the stated reason (CHANGE-035)"
    )


def select_rubric(asset_type: str) -> str:
    if asset_type in {"character", "enemy", "npc", "portrait", "boss", "effect"}:
        return "A"
    if asset_type in {"tileset", "tile", "world_map"}:
        return "B"
    if asset_type in {"parallax", "background"}:
        return "C"
    raise ValueError(f"unknown asset type {asset_type!r}")


def main() -> None:
    import argparse
    from tools._common import load_rgba

    p = argparse.ArgumentParser(description="Score a sprite on the Rubric A automated gate")
    p.add_argument("sprite")
    args = p.parse_args()
    r = score_rubric_a(load_rgba(args.sprite))
    print(f"automated {r['automated_score']}/85 — gate {'PASSED' if r['passed_gate'] else 'FAILED'}")
    for name, c in r["categories"].items():
        print(f"  {name:24s} {c['score']:>2}/{c['max']:<2} {c['evidence']}")


if __name__ == "__main__":
    main()
