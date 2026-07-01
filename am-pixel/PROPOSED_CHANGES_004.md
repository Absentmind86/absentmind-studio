# AM Pixel — Proposed Changes & Additions (Series 004)
**Archive | Version 1.0**

**Status:** CHANGE-032 through CHANGE-038 are **merged into the Bible (v1.6)** and — where they specify code — **implemented in the working tree** in the same session. This file remains as the original rationale record.

Series 004 originates from a comprehensive external review (Fable 5, 2026-07-01) that audited every Bible document and every line of the Phase 0 scaffold. It addresses one architecture-level specification gap, internal contradictions between documents, one licensing-policy contradiction, and code defects in the compliance scaffold. The full review findings are summarized in the session record; this document records only the changes adopted.

---

## CHANGE-032 — Palette Grounding for Token Semantics

**Type:** Core architecture specification gap (closes review finding A2)
**Priority:** Critical — Phase 3 data format and Phase 4 model input depend on it
**Affected:** SPEC §3.1, §3.2; `data/pipeline/indexer.py`; `model/architecture/tokenizer.py`, `conditioning.py`

### Problem

The spec said sprites are generated as palette-index tokens, but every sprite in a scraped corpus has its own palette — "index 3" means a different color in every training example. As specified, Stage 1 foundation training could not teach "palette relationships or shading principles" because token IDs carried no stable color meaning. This gap sat *beneath* documented Risks A–D and was not on the risk register.

### Adopted Solution (two complementary mechanisms)

**1. Canonical ramp-ordered indexing (ingestion-time).** `indexer.py` does not assign palette indices arbitrarily. For every sprite: index 0 is always transparent; remaining colors are clustered into hue ramps (greedy hue-distance clustering in HSV), ramps are ordered by average hue, and colors within a ramp are ordered dark → light. Index positions therefore carry stable *relative* semantics across the whole corpus (low ramp positions = shadows, high = highlights), giving the model a consistent structural signal.

**2. Palette color tokens in the conditioning prefix (train + inference).** The conditioning prefix for every sequence (including Tier 2 corpus sprites with no DNA) begins with one palette descriptor token per palette slot. Each descriptor embeds the slot's actual color as the sum of three learned embeddings over the SNES 15-bit channels (R5, G5, B5 — 32 values each), plus the slot index embedding. The model always knows what color every index refers to. DNA conditioning (Modes 1–6) appends the DNA-derived constraint tokens after the palette block; Mode 7 freeform uses the palette block alone with the full 256-color vocabulary.

Cost: +N conditioning tokens for an N-color palette (typically 15) — negligible against 384–3,072 sprite tokens. Palette-masked sampling at inference is unchanged (logits of out-of-palette indices are masked, which is the precise implementation of "the model cannot generate a color outside the palette").

---

## CHANGE-033 — Rubric B/C Automated/Human Tier Split

**Type:** Consistency fix (review finding B2)
**Affected:** SPEC §8.3

Constitution Rule 1 defines gating as automated 85/85 + human 15 → combined 95, but Rubrics B and C were flat 100-point tables with no tier split, making Rule 1 inapplicable to tilesets and parallax. Adopted split mirrors Rubric A exactly (automated 85 / human 15):

- **Rubric B (tilesets):** Automated 85 = Seam Integrity 30 + Texture Coherence 20 + Visual Recession 20 (contrast/saturation/detail-density heuristics vs. character sprites) + Completeness 10 + Technical Compliance 5. Human 15 = Atmospheric Consistency 15.
- **Rubric C (parallax):** Automated 85 = Layer Seaming 25 + Layer Depth Differentiation 25 + Character Contrast 15 + Atmospheric Cohesion (measurable component: palette/light-direction consistency) 15 + Technical Compliance 5. Human 15 = Emotional Tone 10 + Atmospheric Cohesion (feel component) 5.

---

## CHANGE-034 — Provenance Manifest Write-Safety

**Type:** Data-integrity hardening (review finding C8)
**Affected:** SPEC §15; new `data/pipeline/provenance.py`

A single JSON array rewritten on every ingestion is the most corruption-prone format for an "immutable ledger" at 50k entries. The canonical committed format remains the JSON array (human-reviewable, diff-able), but all writes route through `data/pipeline/provenance.py`, which (a) appends every entry to `data/TRAINING_PROVENANCE_MANIFEST.jsonl` (append-only journal, crash-safe) before (b) atomically rewriting the canonical array via temp-file + `os.replace`. On mismatch, the journal is authoritative and the array is rebuilt from it. Lookup helpers give O(1) membership checks against an in-memory index.

---

## CHANGE-035 — Rebuild Semantics: Two Failure Paths

**Type:** Threshold-definition clarification (review finding B1)
**Affected:** SPEC §8.2; am-pixel/README.md Quality Standard

Documents disagreed about what happens between 85/85 automated and 95 combined. Adopted semantics:

1. **Automated failure (<85/85):** full rebuild from silhouette. The human never sees the sprite (unless 5 consecutive attempts fail, per Mode 1 rules). This is Constitution Rule 4.
2. **Human-gate failure (85/85 automated, combined <95):** the sprite was technically sound but the human found it unoriginal or soulless. It is rejected in the approval UI and regenerated through the standard adjustment loop *with the human's stated reason as conditioning*. A from-silhouette rebuild is not forced — the human may request one.

Constitution Rule 1 and Rule 4 already stated this correctly; README and SPEC §8.2 wording contradicted them and are now aligned.

---

## CHANGE-036 — Hardware Tier Correction: OpenCL → XPU

**Type:** Factual correction (review finding A8)
**Affected:** SPEC §14; ROADMAP Phase 0; OPENCLAW_PROMPT Hardware Context

PyTorch has no supported OpenCL backend; detection tier 4 was unimplementable as written. Tier 4 is now Intel GPU → XPU (`torch.xpu`, supported since PyTorch 2.4). Hierarchy: CUDA → ROCm (presents as `torch.cuda` on ROCm builds) → MPS → XPU → CPU.

---

## CHANGE-037 — Tier 0 Validation Corpus

**Type:** New definition enabling pipeline verification without production data
**Affected:** SPEC §15; FOLDER_STRUCTURE (`data/validation_corpus/`)

The ban on synthetic training data (OPENCLAW_PROMPT — Training Data Approach) exists to prevent quality circularity in the *production* model. It does not — and now explicitly does not — prevent using procedurally generated sprites to smoke-test the pipeline and training code end-to-end. Tier 0 entries are recorded in the provenance manifest with `"tier": 0, "license": "synthetic-validation"`, are excluded from corpus statistics and all pass-rate metrics, and **must never be present in a production training run's data mix** (`training_run_gate` rejects a manifest whose only entries are Tier 0 for production runs; validation runs must be explicitly flagged `--validation-run`).

Rationale for adopting now: the execution environment for the 2026-07-01 session has no network route to any approved data source (OpenGameArt, itch.io, kenney.nl all blocked by network policy). The human explicitly authorized proceeding past this stop. A Tier 0 corpus lets every line of the pipeline, model, training loop, and evaluation stack be proven live so that real Tier 1/2 data can be dropped in with zero code changes.

---

## CHANGE-038 — CC-BY-SA Licensing Hold

**Type:** Legal-consistency fix (review finding A6)
**Affected:** SPEC §15

§15 rejected CC-BY-ND *because "training creates derivatives."* Accepting that premise, CC-BY-SA's share-alike obligation may attach to model weights and/or outputs — incompatible with §12.3's closed commercial tiers. Holding both positions was self-contradictory. CC-BY-SA is moved from "acceptable" to **on hold pending qualified legal review**. No CC-BY-SA material may be ingested until a written legal opinion is added to `data/scraper/sources.md`. CC0, CC-BY (with attribution manifest), and commissioned work-for-hire remain acceptable.

---

*AM Pixel Proposed Changes Series 004 | merged into Bible v1.6 | Absentmind Studio*
