# Model Architecture — Implementation Notes (CHANGE-020)

**Written per Constitution Rule 6 / OPENCLAW_PROMPT Rule 9 after completing
`model/architecture/`. This documents every implementation decision, including
one deviation from the spec's letter (§3, flagged for review).**

**Review status:** PHASE4_ARCHITECTURE_REVIEW remains **PENDING** in
`logs/phase_gates.md` for **production** training. The 2026-07-01 session ran a
**tier-0 validation training run only** (CHANGE-037), under the human's explicit
written authorization of that session ("full authority… ignore that stop and do
what you can moving forward" — recorded in `logs/decision_log.md`). No
production training has occurred. The production gate is untouched and still
requires human approval of this document.

---

## 1. 2D positional encodings (CHANGE-010)

Each slot's embedding sums: `value_emb(prev_value) + x_emb(x) + y_emb(y) +
phase_emb(phase) + channel_emb(r5,g5,b5)`. The X and Y tables are learned
`nn.Embedding(max_canvas=64, d_model)` — not sinusoidal. There is **no 1D
sequence positional encoding anywhere**; slot order enters only through the
causal mask. Conditioning tokens carry `x = y = 0` and a distinct
`phase_emb(PHASE_COND)` — the "separate learned embedding type" the spec
requires for DNA/conditioning tokens.

## 2. Palette grounding (CHANGE-032)

Two halves, both implemented:
- **Canonical indexing** (`data/pipeline/indexer.py`): index 0 = transparent;
  colors clustered into hue ramps (gray ramp first), ramps ordered by hue,
  dark → light within a ramp. Index positions carry stable relative meaning
  corpus-wide.
- **Palette descriptor block** (`conditioning.py`): the prefix contains one
  `PAL` slot per palette color; its embedding adds three learned tables over
  the SNES 5-bit channels (32 values each). The model always knows what color
  every index denotes. Freeform (Mode 7) uses the same block with a larger
  palette and no DNA tokens.

`DNAConditioner` (categorical construction rules: light source, max shades)
exists and is *not yet wired into the training prefix* — Tier 0 sprites carry
no DNA. Wiring it is a Phase 4 task once real DNA-paired data exists.

## 3. DEVIATION — generation order: mask-determined three-phase, not four-category

**The spec's letter:** training sequences ordered transparent → outline →
structural → non-structural (CHANGE-001/014), generated in that order.

**The problem discovered during implementation:** the four-category order is a
function of the *finished sprite* (structural = large same-index regions —
unknowable before the colors exist). In a next-token model, the position of
the next token must be known at sampling time. Generating "structural pixels
before non-structural pixels" requires knowing region sizes before generating
the regions — the order is not well-posed at inference. This is exactly the
class of silent architectural contradiction CHANGE-020 review exists to catch
(cf. the 1D-encoding contradiction the spec itself documents).

**The implemented resolution (mask-determined three-phase order):**
1. **Mask phase** — all H×W positions in raster order; vocabulary restricted
   to {TRANSPARENT, OPAQUE-placeholder}. Commits the silhouette first — the
   spec's stated intent for "transparent pixels first".
2. **Outline phase** — outline positions are a *deterministic function of the
   committed mask* (visible pixels 4-adjacent to transparency/border), raster
   order, palette values. "Outline pixels second" — preserved exactly.
3. **Interior phase** — remaining visible positions, raster order, palette
   values. This merges structural/shade/detail *at the order level*.

Every phase's positions are computable from already-generated content, so
inference is well-posed, and each slot's (x, y) rides in as a query embedding
(§1). Cost: sequence length grows from H·W to H·W + N_visible (a 16×24 sprite:
384 → ~600 tokens; a 48×64 battle sprite: 3,072 → ~5,600). The Risk A
(CHANGE-007) sequence-length concern therefore applies at a lower sprite size
than the spec assumed — the Phase 4 sequence-length experiment gate is MORE
important, not less. Mitigation if needed: run-length-encoded mask phase
(documented, not built — do not build speculatively).

The four/five-category classifier (`pixel_classifier.py`) remains fully
implemented and used for corpus statistics, the 3%-floor gate, and the Phase 4
structure-aware-vs-raster comparison (teacher-forced likelihood evaluation can
use any order). If the Phase 4 experiment shows the full category order is
worth its complexity, the upgrade path is order-token prediction (the model
emits (position, value) pairs) — a documented post-experiment decision.

## 4. Causal mask × structure-aware ordering

Standard upper-triangular causal mask over the full sequence (conditioning
block + all three phases). Because canvas position is a query embedding, the
causal mask constrains *information flow* (later slots see earlier slots),
not *spatial order*. Spatially-adjacent pixels far apart in the sequence still
attend to each other through their X/Y embeddings. The conditioning block is
visible to every sprite token (it precedes them), implementing prefix
conditioning per SPEC §3.4 Risk B; loss is computed only on sprite-phase slots
(`target_mask`), never on conditioning.

## 5. Vocabulary layout

`0` transparent · `1..255` palette indices · `256` BOS · `257` SEP ·
`258` PAL (descriptor slot) · `259` OPQ (mask-phase placeholder). Sampling is
hard-masked per phase: mask phase → {0, OPQ}; outline/interior → {1..n_palette}.
The palette constraint is enforced by construction at every step — the literal
meaning of "conditioning collapses the valid token space".

## 6. Model sizes

- `small` (CPU proof-of-life): d=128, 4 layers, 4 heads, ~1.3M params.
- `base` (Phase 4 target): d=384, 10 layers, 6 heads — sized for a 10GB GPU
  with gradient checkpointing headroom. Hyperparameters are a Phase 4 tuning
  task, not a commitment.

## 7. Known gaps deferred to Phase 4+ (explicitly not built speculatively)

- Cross-attention conditioning (Risk B upgrade) — build only if the top/bottom
  half `dna_diff` delta exceeds 10% (SPEC gate).
- Temporal frame conditioning / pose tokens (Risk C, CHANGE-015).
- Hierarchical generation (Risk A) — gate: >1,500-token pass rate < 70%.
- KV-cache for generation (currently full recompute per token — correctness
  first, speed third; Constitution Rule 8).
- View-pair training format `[DNA]+[Brief]+[View A] → [View B]` (CHANGE-017) —
  detector/annotator are built; the training-side pair batching needs real
  paired data.

## 8. Test evidence

`tests/test_model.py`: tokenizer phase layout verified; forward/loss shapes;
a 2-layer model overfits a single sprite (loss falls >75% in 220 steps —
gradient flow through all five embedding paths confirmed); generation respects
the palette mask exactly; checkpoint save/load roundtrips.

---

*Prepared 2026-07-01. Production training remains gated on human review of
this document (Constitution Rule 6).*
