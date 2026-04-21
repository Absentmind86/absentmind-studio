# AM Pixel — Proposed Changes & Additions (Series 002)
**Archive | Version 0.3**

**Status:** Substantive proposals (CHANGE-010 through CHANGE-023) are **merged into the Bible** (`SPEC.md`, `ROADMAP.md`, `FOLDER_STRUCTURE.md`, `OPENCLAW_PROMPT.md`, and related docs). The Phase 0 **on-disk** layout and stubs under `am-pixel/` match this series. This file stays in the repo as the **original rationale and review record** — not as a pending work queue.

This document recorded proposed changes identified through external architecture review sessions. Each item includes the rationale, the affected documents, and the proposed implementation.

All changes in this document were identified after v1.2 of the spec was locked. They do not supersede PROPOSED_CHANGES.md (Series 001) — that document is now fully implemented in v1.2.

---

## CHANGE-010 — 2D Positional Encodings for Structure-Aware Token Ordering

**Type:** Core architecture fix
**Priority:** High — without this, CHANGE-001 (structure-aware ordering) may actively harm spatial coherence
**Affected documents:** SPEC.md (§3.1, §3.2), FOLDER_STRUCTURE.md (`model/architecture/tokenizer.py`, `conditioning.py`)

### Problem

SPEC.md §3.2 states that structure-aware token ordering uses "positional encodings that preserve the original (x, y) canvas coordinates." This is correct in intent but unspecified in implementation — and the default positional encoding used in GPT-style transformers (sinusoidal or RoPE) is **1D**. It encodes position in the token *sequence*, not position on the *canvas*.

When the token sequence is reordered from raster to structure-aware order, the spatial relationship between tokens is scrambled. Token 1 (transparent, canvas position 0,0) and Token 847 (outline, canvas position 15,5) may be spatially adjacent on the canvas but 846 positions apart in the sequence. A 1D positional encoding tells the model they are far apart — which is correct sequentially but wrong spatially. The model must then learn incredibly indirect relationships to reconstruct spatial adjacency from sequence distance. This is not impossible, but it is the wrong constraint to impose on a model that is simultaneously trying to learn what pixel art looks like.

This is not a reason to abandon structure-aware ordering — it is a reason to specify the positional encoding correctly.

### Proposed Fix

Replace 1D positional encodings with **2D positional encodings** at the input layer of the transformer. Each token receives two independent learned embeddings: one for its canvas X coordinate and one for its canvas Y coordinate. These are summed and added to the token embedding before the first attention layer, exactly as done in Vision Transformer (ViT) architectures.

The causal mask does not need to change. The model attends causally across the reordered sequence as usual. The difference is that every token now carries its true canvas position regardless of where it falls in the generation sequence. The model can learn spatial adjacency relationships directly from the embeddings rather than having to infer them from sequence distance.

### Implementation Notes

- `model/architecture/tokenizer.py`: Each token in the sequence carries a `(canvas_x, canvas_y)` coordinate pair in addition to its palette index value. These coordinates are preserved through the reordering step.
- `model/architecture/transformer.py`: Input embedding layer sums three components: palette index embedding + learned X position embedding + learned Y position embedding. Standard 1D sequence position encoding is removed or kept only as a secondary signal — the canvas 2D coordinates are primary.
- `model/architecture/conditioning.py`: DNA conditioning tokens are positioned at sequence positions 0..N before the sprite token sequence begins. They do not carry canvas coordinates (they are not canvas pixels). They use a separate learned embedding type to distinguish them from sprite tokens.
- `data/pipeline/sequence_reorderer.py`: Must preserve and output `(canvas_x, canvas_y)` alongside each reordered token. The output format is a list of `(palette_index, canvas_x, canvas_y)` tuples, not just palette indices.

### Risk

Low-to-medium. 2D positional encodings are well-established in vision transformers. The implementation change is localized to the input embedding layer. The main risk is implementation error — ensure the coordinate embedding lookup tables are trained (not fixed sinusoidal) and correctly initialized.

---

## CHANGE-011 — MaskGIT as a Phase 4 Architectural Experiment

**Type:** Architectural alternative — document and evaluate, do not pre-adopt
**Priority:** Medium — worth knowing about before Phase 4, but not a pre-Phase-0 decision
**Affected documents:** SPEC.md (§3.1, §3.4), ROADMAP.md (Phase 4)

### Problem

Multiple external reviewers have correctly identified that autoregressive generation is sequential: to generate token N, the model must have generated tokens 1 through N-1. For a 48×64 battle sprite (3,072 tokens), this means 3,072 sequential forward passes. Generation will be measurably slower than diffusion-based alternatives.

### Design Position

**Speed is explicitly not a primary concern for AM Pixel MVP.** Accuracy and palette fidelity are the only criteria that matter for v1. Generation can be slow. A sprite that takes 30 seconds to generate but is pixel-perfect is the correct tradeoff. Speed optimizations are post-MVP work.

See `README.md` — On Speed vs. Accuracy for the full position statement.

### What MaskGIT Is (For Reference)

Masked Generative Transformers (MaskGIT) use the same discrete vocabulary as the current architecture (palette indices) but generate iteratively rather than sequentially. All tokens are predicted simultaneously in each iteration; low-confidence predictions are masked and re-predicted in subsequent iterations (typically 8–12 rounds). This is 10–100× faster than autoregressive inference while preserving discrete token generation.

MaskGIT requires a **bidirectional** transformer (not causal), which changes the conditioning architecture — DNA conditioning cannot be a prefix in a bidirectional model; it must be injected via cross-attention or added as special tokens visible to all positions. This is a meaningful architectural change, not a drop-in replacement.

### Phase 4 Experiment

If inference speed becomes a practical blocker during Phase 4 or 5 validation (i.e., generating the required batch sizes takes so long it makes iteration impossible), MaskGIT should be evaluated as an alternative architecture at that point — not before. The comparison should be documented in `logs/training_log.md`.

Add the following to the ROADMAP Phase 4 section as an optional experiment gate:

> *If generating 100 sprites for the Phase 4 evaluation batch takes longer than 4 hours of wall-clock time on the available hardware, document the bottleneck and evaluate MaskGIT as an alternative architecture before proceeding to Phase 5. This is an optional gate — only triggered if speed is a demonstrated blocker, not a theoretical one.*

### Risk

Low for documentation. Medium if MaskGIT is actually adopted — it requires re-architecting the conditioning system.

---

## CHANGE-012 — Sliding Window Conditioning for Tileset Generation

**Type:** Core feature gap — Mode 3 cannot work without this
**Priority:** High — without it, seamless tileset generation has no defined mechanism
**Affected documents:** SPEC.md (§5.3, §3.3), FOLDER_STRUCTURE.md (`model/architecture/conditioning.py`)

### Problem

SPEC.md §5.3 specifies that every tile must pass seam validation — all four edges must tile seamlessly with their neighbors. If a tile fails, it is rebuilt. But the spec does not define how the model generates seam-aware tiles in the first place. Currently the model generates each tile conditioned only on the DNA/Tileset Anchor — it has no information about what the adjacent tile looks like at the boundary. A tile generated in isolation has no reason to produce an edge that matches its neighbor.

The seam validator catches failures after the fact. But without a conditioning mechanism that provides boundary context *before* generation, the model is guessing at seam edges and failures will be frequent and expensive.

### Proposed Fix — Sliding Window Boundary Conditioning

When generating tile at canvas position (x, y), prepend the following as hard conditioning tokens before the tile generation sequence begins:

- **Right edge of tile (x-1, y):** The rightmost column of pixels from the already-approved left neighbor tile (16 tokens for a 16×16 tile)
- **Bottom edge of tile (x, y-1):** The bottom row of pixels from the already-approved upper neighbor tile (16 tokens for a 16×16 tile)

These boundary tokens are flagged as "seam context" — they are not generated, they are ground truth constraints. The model generates the new tile knowing exactly what palette indices must appear at its left and top edges.

For tiles with no left neighbor (leftmost column), no left seam context is prepended. For tiles with no upper neighbor (top row), no upper seam context is prepended.

### Implementation Notes

- `model/architecture/conditioning.py`: Add a `seam_context` conditioning input type alongside the existing DNA conditioning. Seam context tokens are prepended after DNA tokens but before the sprite token sequence. They carry their canvas coordinates via 2D positional encoding (CHANGE-010) so the model knows they represent the boundary region.
- `pipeline/modes/mode3_tileset.py`: Tileset generation must proceed in raster order (left-to-right, top-to-bottom) so that neighbor tiles are always available before the current tile is generated. Random or parallel tile generation is not permitted.
- `tools/seam_validator.py`: When a tile fails seam validation, the rebuild must include the same seam context conditioning that was used in the original attempt, plus a failure annotation token or adjusted temperature. Simply re-generating with identical inputs will produce identical failures.
- The feedback mechanism for failed seams: `rubric_scorer.py` returns the specific failed edge (left, right, top, bottom) and the delta between the tile edge and the neighbor edge. This delta is added to the generation prompt as a natural language note: *"Left edge failed: palette index mismatch at rows 4, 7, 11. Regenerate with tighter left edge constraint."*

### Risk

Medium. This is the most architecturally novel addition in this change set. The sliding window approach is well-established in image generation literature (PixelCNN, etc.) but requires careful coordination between the tileset generation pipeline and the conditioning system. Test on a small 2×2 tile grid before scaling.

---

## CHANGE-013 — Decouple Automated and Human Rubric Scoring

**Type:** Evaluation architecture fix — significant
**Priority:** High — the current rubric design is not fully automatable and will either block the pipeline or produce meaningless scores
**Affected documents:** SPEC.md (§8.2, §8.3), ROADMAP.md (Phase 4, Phase 5, Phase 6, Phase 8)

### Problem

Rubric A awards 5 points for "Soul" and 10 points for "Originality." The spec states that every sprite is evaluated before the human sees it and cannot pass below 95. This means `rubric_scorer.py` must score Soul and Originality programmatically to gate sprite presentation.

This is not feasible. A Python script cannot reliably determine whether a sprite has personality or whether it is too derivative of a specific reference sprite. Any implementation will either:

**A)** Always award the points (making the criteria meaningless), or
**B)** Use perceptual hashing against the training corpus, which will fail constantly because SNES pixel art relies heavily on established visual conventions — a guard sprite *will* look like other guard sprites by design.

More critically: blocking the automated pipeline on a subjective criterion means OpenClaw could get permanently stuck generating rebuild after rebuild of sprites that pass all technical criteria but fail an unimplementable aesthetic check.

### Proposed Fix

**Split Rubric A into two tiers:**

**Tier 1 — Automated Gate (85 points):** All criteria that can be evaluated programmatically with existing tools.

| Category | Points | Evaluated By |
|----------|--------|--------------|
| Technical Compliance | 25 | `palette_validator.py`, `anti_aliasing_detector.py` |
| Construction Quality | 25 | `banding_detector.py`, `outline_checker.py`, `dna_diff.py` |
| Readability | 20 | Silhouette analysis, pixel-level contrast checks |
| Animation Quality | 15 | `effect_timing_evaluator.py` (for effects); pose consistency check for walk cycles |
| **Automated Gate** | **85/85** | **Sprite presented to human if and only if this passes** |

**Tier 2 — Human Gate (15 points):** Awarded by the human in the approval UI.

| Category | Points | Evaluated By |
|----------|--------|--------------|
| Originality | 10 | Human judgment — does this feel fresh or is it a direct copy of a known sprite? |
| Soul | 5 | Human judgment — does this sprite have personality? |
| **Full Score** | **100/100** | **Combined automated + human score** |

**Passing threshold remains 95/100.** A sprite that scores 85/85 automated + 10+/15 human = 95+ passes. A technically perfect sprite that the human finds derivative or lifeless fails and is rebuilt.

### Changes to Phase Gates

All phase gates that reference "95+ rubric score" for automated batch evaluation must be understood as "85/85 automated score" for the purposes of unattended batch runs. Human scoring applies during the approval workflow, not during batch validation.

The 99/100 batch production threshold applies to the automated 85-point gate during unattended batch runs. Human review is applied to every individual sprite presented through the approval UI.

### Changes to the Approval UI

The approval UI must display both scores separately:
- Automated score: `[score]/85 — PASS / FAIL`
- Human score input: Two sliders or numeric inputs — Originality (0–10) and Soul (0–5)
- Combined score: displayed after human input, must reach 95 to confirm approval

### Refinement — Context-Aware Soul Scoring (REFINEMENT-013A)

The Soul criterion as written treats memorability as universally desirable. It is not. Character role determines what "good Soul" means:

**Foreground characters** (player characters, named NPCs, bosses, quest-givers): Soul means personality and distinctiveness. A forgettable player character is a failure.

**Background characters** (generic townspeople, crowd fillers, ambient NPCs): Soul means successful anonymity. A townsperson who reads as too distinctive pulls player attention away from the characters who are supposed to stand out. Overdesigned background characters are a design failure of the opposite kind — they visually compete with named characters and muddy the visual hierarchy of the scene.

This is not a trivial distinction. In a well-designed RPG town, named NPCs pop because the background characters recede. That visual hierarchy is intentional craft, not laziness.

**Implementation:** The approval UI must present a character role dropdown before the human scores Soul:

- **Foreground** (player, named NPC, boss, villain, party member) → Soul scored normally: 0–5 for personality and distinctiveness
- **Background** (generic townsperson, crowd NPC, ambient filler) → Soul criterion renamed to "Visual Hierarchy" and scored inversely: 0–5 for successful visual recession — does this character read as background? Does it avoid competing with foreground characters?

The scoring range (0–5) and the combined 100-point total remain unchanged. Only the meaning of the criterion shifts based on declared role. This role declaration also feeds into the Originality criterion — a generic townsperson is expected to look generic and should not be penalized for resembling other generic townsperson sprites.

### Risk

Low. This is a clarification of intent, not an architectural change. The automated tooling is unchanged. The rubric scoring logic is extended with a human-input pathway in the UI.

---

## CHANGE-014 — Pixel Classifier Simplification for Foundation Training

**Type:** Data pipeline pragmatism fix
**Priority:** Medium — affects training data quality and pipeline reliability
**Affected documents:** SPEC.md (§3.2), FOLDER_STRUCTURE.md (`data/pipeline/pixel_classifier.py`)

### Problem

The current spec defines five pixel categories for structure-aware ordering: transparent, outline, fill, shade, detail. The shade/detail boundary is semantically ambiguous in raw indexed bitmap data without understanding the artistic context of the sprite. A highlight on shiny armor could be classified as either "shade" (part of a light ramp) or "detail" (a specific feature). A rule-based classifier operating on adjacent pixel relationships will produce inconsistent results across the varied quality levels present in scraped training data — particularly OpenGameArt sprites, which range from professional to amateur with no consistent shading discipline.

Inconsistent classification = inconsistent token ordering = inconsistent training signal = model that learns nothing coherent from structure-aware ordering.

### Proposed Fix

**For Stage 1 (Foundation Training):** Collapse shade and detail into a single category. The classifier produces four categories only:

1. **Transparent** — alpha = 0
2. **Outline** — non-transparent pixels adjacent to transparent pixels
3. **Structural** — large contiguous regions of a single palette index (replaces "fill")
4. **Non-structural** — everything else (replaces "shade" + "detail" combined)

This distinction is reliable from pixel data alone: transparent/outline/structural are geometrically definable. Non-structural captures everything the classifier cannot confidently distinguish.

Generation order becomes: Transparent → Outline → Structural → Non-structural.

**For Stage 2 (Quality Fine-Tuning):** The full five-category classification (adding the shade/detail split back) may be applied to the curated fine-tuning dataset, which consists of approved production sprites of known quality. At this stage, the classifier output can be human-verified on a sample basis before use.

### Implementation Notes

- `data/pipeline/pixel_classifier.py`: Implement the four-category version for Phase 3. Add a `--full-five-category` flag for Phase 6 fine-tuning use, disabled by default.
- `data/corpus_stats.md`: Log the distribution of all four categories across the training corpus. Flag any sprite where non-structural pixels exceed 60% of total pixels — this may indicate a misclassified or unusually complex sprite that should be reviewed.

### Risk

Low. Simplifying the classifier reduces implementation complexity and improves reliability. The four-category ordering still preserves the core benefit of structure-aware generation (silhouette committed before fill, fill committed before detail). The shade/detail split is a refinement, not a foundational requirement.

---

## CHANGE-015 — Skeletal Pose Tokens as Animation Upgrade Path

**Type:** Architecture upgrade path documentation
**Priority:** Medium — adds depth to the existing Risk C documentation
**Affected documents:** SPEC.md (§3.4 Risk C)

### Problem

The current Risk C documentation proposes conditioning Frame 2 on Frame 1's raw pixel token sequence. A valid concern has been raised: conditioning on the exact pixel sequence of the previous frame creates pressure toward copying rather than transforming. The model sees 3,072 specific palette indices and must learn to selectively move subsets of them while leaving others intact. This is learnable, but it is a difficult implicit task.

A more structured approach would give the model an explicit representation of *motion* rather than *state*.

### Proposed Upgrade Path (Supplement to Risk C)

If raw-token temporal conditioning (the current Risk C upgrade path) produces stiff or copy-prone animation after evaluation, the next step before declaring the problem unsolvable is **skeletal pose token conditioning**.

**How it works:**

Before training animation sequences, run a preprocessing step that extracts a simplified 2D skeleton from each frame — a small set of key point coordinates representing head center, torso center, and approximate limb endpoints. For a 16×24 world sprite, this might be 6–8 key points. For a 48×64 battle sprite, 10–12.

Key points are extracted using a lightweight rule-based approach: center of mass of the head color region, center of mass of the torso region, extremal pixels of limb regions. This does not require a neural network pose estimator.

Frame 2 is then conditioned on:
- DNA (character identity)
- Brief (feature inventory)
- Frame 1 skeleton tokens (motion context — where things were, compactly)
- NOT Frame 1 raw pixel tokens

The model learns: "The torso moved 0 pixels, the right foot moved +2x, the left foot moved -2x" as a structured input rather than having to infer motion from 3,072 raw token deltas.

**Key advantages:**
- Skeleton tokens are ~10–12 tokens vs 384–3,072 raw pixel tokens — dramatically reduces context length
- Motion is represented explicitly rather than implicitly
- The model is not pressured to copy — it receives positional deltas, not pixel values

**Implementation:** This is a Phase 7–8 upgrade path, only if frame-independent generation fails the Animation Quality rubric and raw-token temporal conditioning also proves insufficient. Do not build speculatively.

Add to `data/pipeline/` a stub file `pose_extractor.py` in Phase 0 — documented interface only, not implemented.

### Risk

Low for documentation. Medium for implementation — pose extraction is only reliable for sprites with clearly distinct color regions per body part, which varies across the corpus.

---

## CHANGE-016 — Brief as Feature Inventory + Twin Input for Multi-View Generation

**Type:** Core architecture gap — affects DNA system and Mode 1 fundamentally
**Priority:** High — without this, multi-view character generation is architecturally incomplete
**Affected documents:** SPEC.md (§4.1, §4.2, §4.3, §4.4, §5.1), ROADMAP.md (Phase 2, Phase 7)

### Problem

The DNA system extracts its specification from the pixels of the approved master sprite. This is correct for everything that is visible in that sprite. It is a fundamental failure for everything that is not visible.

**The Backpack Problem:**
A character is designed as "old wizard with a large backpack and a ponytail hidden under his hood." The user approves the front-facing sprite. The DNA is extracted from those pixels. The DNA correctly records: robe color, beard color, skin tone, outline style, proportions. It does not and cannot record: backpack (hidden behind body), ponytail (hidden by hood), rear armor plate, tail, wings, or any other feature occluded in the master view.

When the side view is generated from DNA alone, the model produces: the same wizard, without the backpack. Because the DNA has no record of the backpack existing.

This is not a edge case. It is the standard situation for any character with depth — which is every interesting character.

### Root Cause

DNA extraction is pixel-based. Pixels can only encode what is visible. The text brief — written by the human before generation — contains the complete feature inventory including occluded features. Once generation begins, the brief is currently not preserved as a required input for subsequent view generation.

### Proposed Fix — Two-Part

**Part 1: Brief as Required Feature Inventory**

The `brief` field in the DNA schema must be elevated from flavor text to a required complete feature inventory. The DNA lock warning must explicitly prompt the user to confirm the brief is complete before locking — because the brief is the only record of occluded features.

Add to the DNA lock warning:

> *"Before locking DNA, confirm that your character brief is complete. The brief must describe ALL features of this character — including features not visible in the current sprite (backpacks, tails, ponytails, rear armor, hidden accessories). The brief is the only source of truth for features that are occluded in the master view. Once DNA is locked, multi-view generation will use the brief to render hidden features. If the brief is incomplete, those features will not appear in side or rear views."*

The DNA schema `brief` section should be extended to include an explicit `occluded_features` field:

```json
"brief": {
  "personality": "Gruff and battle-worn, speaks in short sentences",
  "role": "Player character — warrior class",
  "defining_trait": "Missing left eye, covered by leather patch",
  "occluded_features": [
    "Large iron-frame backpack with bedroll strapped to top",
    "Long brown ponytail reaching mid-back, tied with red cord",
    "Rear pauldron with clan sigil on right shoulder blade"
  ]
}
```

**Part 2: Twin Input for View Generation**

The Mode 1 flow must be updated. When generating any non-master profile (side view, rear view, chibi), the generation input must be:

`[DNA] + [Complete Brief including occluded_features] + [Master View Tokens]`

Not just `[DNA]`.

This gives the model three information sources:
- **DNA:** Exact colors, proportions, outline style — character identity
- **Brief:** Complete feature inventory including hidden features — character completeness
- **Master View Tokens:** Exact pixel state of the approved front-facing sprite — visual grounding

The model can learn: "The brief says backpack. The front view shows no backpack. Therefore: backpack appears on the side/rear view."

### Training Implication

The paired-view training data strategy (CHANGE-017) must include text brief annotations alongside image pairs. A training example of Front → Side that lacks text annotation cannot teach occluded feature handling. Annotated pairs are higher value than unannotated pairs and should be prioritized in the corpus even if they are rarer.

### Implementation Notes

- `dna/characters/[character_id].json`: Schema updated with `occluded_features` array field
- `pipeline/approval/conversation.py`: DNA lock flow must prompt for occluded features explicitly before lock confirmation
- `pipeline/modes/mode1_character.py`: Non-master profile generation updated to include master view tokens as conditioning input
- `tools/dna_extractor.py`: After extraction, display a summary of what was extracted from pixels and prompt: *"Are there any features of this character not visible in this sprite? Add them to the brief before locking."*

### Risk

Medium. The twin input conditioning (DNA + Brief + Master View Tokens) increases the context length for non-master profile generation but is well within bounds for standard sprite sizes. The main risk is training data availability — paired front/side sprites with text annotations are rare in open-licensed sprite archives. The model may need to learn view rotation primarily from unannotated pairs and rely on the brief for occluded feature injection at inference time.

---

## CHANGE-017 — Paired View Training Sequences for Rotation Learning

**Type:** Training data pipeline addition
**Priority:** High — without structured view-pair training data, multi-view generation relies entirely on generalization from single-view data
**Affected documents:** SPEC.md (§3.2), ROADMAP.md (Phase 3), FOLDER_STRUCTURE.md (`data/pipeline/`)

### Problem

The model is currently trained on individual sprites. When it needs to generate a side view of a character it has only seen from the front, it has no learned representation of what "rotating a character" means spatially. It must generalize this from texture and proportion patterns in its training data — which may or may not contain enough multi-view examples to develop reliable rotation geometry.

The specific skills required for multi-view generation — understanding that a nose disappears as the face rotates, that shoulder width contracts in side view, that a backpack emerges from behind the torso — are learnable from data but only if the training data explicitly demonstrates these transitions.

### Proposed Fix

**Identify and preserve paired-view sprites during data collection.**

Many sprite sheets in the wild contain sprites of the same character from multiple directions — this is standard for RPG walk cycles. The data pipeline must actively identify these pairs rather than treating each direction as an independent sprite.

**Detection heuristic:** Sprites on the same sprite sheet that share a dominant palette, similar silhouette area, and similar proportions are candidate view pairs. Flag these for human review during corpus curation. Confirmed pairs are stored with a `view_pair_id` linking them.

**Training sequence structure for view pairs:**

Standard single-view training:
`[DNA] + [Sprite Tokens]` → next token prediction

Paired-view training (higher weight in training mix):
`[DNA] + [Brief] + [View A Tokens]` → `[View B Tokens]` — the model predicts View B given View A

The paired-view sequence teaches the model what changes between views (pose, silhouette, visible features) while what stays constant is enforced by the shared DNA.

**Target corpus composition:**
- Stage 1 training target: At minimum 20% of training examples should be paired-view sequences
- If paired sprites are insufficient in scraped data, supplement with programmatically generated pairs: take a front-facing sprite, apply a simple reflection to approximate a rear view, use as a low-quality pair. Label these as synthetic pairs with lower training weight than confirmed pairs.

**New pipeline files:**

- `data/pipeline/view_pair_detector.py` — identifies candidate view pairs within sprite sheets using palette similarity and proportion matching heuristics
- `data/pipeline/pair_annotator.py` — presents candidate pairs for human confirmation during corpus curation; writes confirmed pairs with `view_pair_id` and view direction labels

**Corpus stats addition:**
`data/corpus_stats.md` must log: total paired sequences, confirmed vs synthetic pairs, view direction coverage (how many Front→Side, Side→Back, Front→Back pairs exist in corpus).

### Risk

Medium. The main risk is that paired sprites in open-licensed archives are fewer than expected, forcing reliance on synthetic pairs. Synthetic pairs (reflection-based) teach the model symmetry but not true rotation — a reflected sprite is not a true side view. Document the synthetic pair ratio and re-evaluate if it exceeds 50% of all pairs.

---

## CHANGE-018 — Document Changelogs

**Type:** Document hygiene — applies to all spec documents
**Priority:** Medium — important for long-term maintainability and for OpenClaw's ability to understand what changed between versions
**Affected documents:** SPEC.md, ROADMAP.md, GENRE_TAXONOMY.md, FOLDER_STRUCTURE.md, OPENCLAW_PROMPT.md, README.md

### Problem

As the spec documents evolve through multiple rounds of refinement, there is no record of what changed between versions, why it changed, or what prompted the change. This creates two problems:

1. A human returning to the project after time away cannot quickly understand what has been updated
2. OpenClaw, which reads these documents fresh each session, cannot distinguish new decisions from original decisions — and therefore cannot know whether its understanding of a previous version is still valid

### Proposed Fix

Add a `## Changelog` section to the bottom of every spec document. Each entry records: version number, date, a clear description of what changed, and the reason for the change.

**Format:**

```markdown
---

## Changelog

### v1.2 — 2026-04-11
- Added structure-aware token ordering (CHANGE-001): training sequences reordered transparent→outline→fill→shade→detail to mirror professional construction process
- Added prompt expansion layer (CHANGE-002): optional brief expansion for character creation modes
- GPU backend universalization (CHANGE-003): replaced CUDA-only requirement with hardware detection hierarchy
- Restored missing §6 Project Organization header (CHANGE-004)
- Fixed OpenClaw prompt document list and added forced confirmation paragraph (CHANGE-005)
- Added folder structure entries for hardware detector, log placeholders, am-pixel/README (CHANGE-006)
- Documented sequence length error accumulation as Risk A §3.4 (CHANGE-007)
- Documented DNA conditioning dilution as Risk B §3.4 (CHANGE-008)
- Documented animation temporal coherence gap as Risk C §3.4 (CHANGE-009)

### v1.1 — [original release date]
- Initial v1.1 release
```

Each document's changelog should begin with its current version (v1.2) and work backward only as far as records allow. Future changes to any document must include a changelog entry at the time of the change — not reconstructed later.

### Implementation

This is a pure documentation task. No code changes. Apply to all six documents when implementing any change from this series. The changelog section goes at the very bottom of each document, after all content, separated by a horizontal rule.

---

## CHANGE-019 — Golden Dataset Strategy for Phase 3 Data Pipeline

**Type:** Training data strategy — significant scope revision
**Priority:** High — directly affects whether the foundation model learns anything useful
**Affected documents:** SPEC.md (§3.2), ROADMAP.md (Phase 3)

### Problem

Phase 3 targets 50,000 sprite sequences scraped from OpenGameArt.org and itch.io free packs. This target is based on an optimistic assumption about open-source sprite quality that does not reflect reality.

The open-source pixel art ecosystem contains an overwhelming proportion of unusable material: pillow-shaded amateur work, 32-bit color PNGs presented as pixel art, sprite sheets with non-standard layouts, padding offsets, composite backgrounds, and sprites that mix styles inconsistently within a single sheet. The `validator.py` SNES compliance filter will reject the majority of what is scraped. More critically, sprite sheet extraction is a genuinely unsolved algorithmic problem — sheets are rarely perfectly gridded, and extracting individual sprites programmatically produces a high rate of misaligned, clipped, or merged extractions.

An autoregressive transformer trained on discrete palette-index tokens is more sensitive to data quality than most architectures. It learns exact token distributions. If the training data contains noisy, inconsistently extracted sprites, the model learns to generate noise with SNES-adjacent colors. Garbage in, garbage out applies with unusual force here.

### Proposed Fix — Two-Tier Corpus Strategy

**Tier 1 — Golden Dataset (primary training signal):**
A manually curated set of 3,000–5,000 sprites that are individually verified to be: correctly extracted from their source sheets, SNES-aesthetic compliant, correctly palette-indexed, free of pillow shading and banding, and representative of the asset types AM Pixel must generate (characters, tilesets, effects, UI).

This set is small but clean. It is the primary source of the model's quality signal. Every sprite in this set has been human-reviewed.

Building this dataset is not a scripted task. It requires someone with pixel art knowledge to look at each sprite and confirm it meets the construction standards. This is the most important work in Phase 3 and it should be treated as such — not as a cleanup pass after scraping, but as the primary Phase 3 deliverable.

**Tier 2 — Broad Corpus (volume training):**
The algorithmically scraped and filtered corpus, target 30,000–50,000 sprites. Used for foundation training to give the model exposure to variety. Quality is lower and inconsistent. This corpus teaches the model what pixel art looks like in general — the Golden Dataset teaches it what good pixel art looks like specifically.

Training strategy: pre-train on Tier 2 (broad exposure), fine-tune on Tier 1 (quality signal). This mirrors the two-stage training pipeline already in the spec — Stage 1 foundation, Stage 2 quality fine-tuning. Tier 2 = Stage 1 corpus. Tier 1 = Stage 2 corpus.

### Changes to Phase 3

- Add `data/golden/` directory to FOLDER_STRUCTURE.md — manually curated sprites stored separately from the broad corpus
- Add `data/golden/curation_log.md` — records every sprite in the golden set with source, extraction method, and human reviewer notes
- Phase 3 completion gate must include: Golden Dataset contains minimum 3,000 sprites, each individually verified
- Phase 3 time allocation should be treated as 3× the original estimate — manual curation is slow and cannot be rushed
- `data/corpus_stats.md` must report Tier 1 and Tier 2 statistics separately

### Risk

Medium-high operationally. Manual curation of 3,000+ sprites is significant human effort — the largest single time investment in Phase 3. There is no shortcut. The alternative is a model that generates mediocre sprites consistently, which defeats the entire purpose of the project.

---

## CHANGE-020 — OpenClaw Architecture Review Gate for Core Model Files

**Type:** Process safeguard — human review requirement
**Priority:** High — prevents silent failure on the most technically demanding components
**Affected documents:** OPENCLAW_PROMPT.md, ROADMAP.md (Phase 4)

### Problem

External reviewers have consistently raised a concern that deserves direct acknowledgment: current AI coding agents, including OpenClaw, may struggle to implement novel ML architecture components correctly without human validation. Specifically:

- 2D positional encoding implementations have subtle initialization requirements
- Custom attention conditioning for DNA prefix tokens requires careful masking
- CUDA/device-agnostic training code has common failure modes that are hard to catch without running the training loop
- PyTorch API hallucination is a documented failure mode for coding agents on less common operations

The spec's escalation protocol handles blockers (48-hour rule, BLOCKERS.md). But a subtly wrong implementation of 2D positional encodings won't block — it will appear to work, train without errors, and produce plausible-looking output that scores poorly on the rubric for reasons that are hard to diagnose. Silent failure is worse than a documented blocker.

### Proposed Fix — Mandatory Human Review Gate for Core Architecture Files

Add a mandatory human review requirement to Phase 4, specifically for the following files before any training run begins:

- `model/architecture/transformer.py` — core model architecture
- `model/architecture/conditioning.py` — DNA conditioning encoder
- `model/architecture/tokenizer.py` — palette index tokenizer with 2D positional encodings
- `model/architecture/config.py` — model hyperparameters

**Gate requirement:** OpenClaw builds these files, documents its implementation decisions in a `model/architecture/IMPLEMENTATION_NOTES.md` file, then halts and flags for human review before running any training. The human reviews the implementation notes and the code, confirms the architecture matches the spec, and explicitly approves proceeding to training.

This is not a lack of confidence in OpenClaw — it is standard engineering practice. Novel ML architecture code should be reviewed by a human before committing GPU hours to a training run based on it.

### Addition to OPENCLAW_PROMPT

Add to the Non-Negotiable Rules section:

> **9. Core architecture files require human review before training.**
> After completing `model/architecture/`, write `model/architecture/IMPLEMENTATION_NOTES.md` documenting every implementation decision made in those files, including: how 2D positional encodings are implemented, how DNA conditioning tokens are handled, how the causal mask interacts with the structure-aware token ordering. Then halt and flag for human review. Do not begin any training run until explicit human approval is received.

### Risk

Low. This adds one human review checkpoint. It does not change the architecture or the training process — only adds a gate before the first training run begins.

---

## CHANGE-021 — VLM Critic as Evaluation Engine Upgrade Path

**Type:** Evaluation engine upgrade path documentation
**Priority:** Medium — relevant if automated heuristics produce systematic false positives or negatives
**Affected documents:** SPEC.md (§8.4)

### Problem

CHANGE-013 correctly decoupled automated scoring (85 points of hard math) from human scoring (15 points of aesthetic judgment). However a valid concern has been raised about the automated 85 points: certain Construction Quality criteria are more contextual than they appear in code.

Specific examples:
- **Banding detection:** Cylindrical shading on a metal pipe looks like banding algorithmically. It isn't. A `banding_detector.py` will flag it incorrectly.
- **Pillow shading:** Pillow shading is a radial gradient of palette indices. So is a legitimate spherical highlight on a round object. The algorithm cannot distinguish them without understanding what the object is.
- **Outline color:** The spec correctly flags pure black outlines (should be darkened local color). But a character wearing a black robe has outline pixels that are legitimately black. The algorithm will fail the sprite incorrectly.

These are contextual judgments that require understanding what the sprite depicts — not just what its hex values are. Python heuristics operating on raw pixel data cannot make these distinctions reliably and will produce false positives that either block good sprites or get tuned so loosely they stop catching actual failures.

### Proposed Upgrade Path

If automated heuristics produce systematic false positive rates above 10% during Phase 5 Practice Gauntlet validation, consider augmenting or replacing the problematic heuristic tools with a **Vision-Language Model (VLM) critic**.

**How it works:** A VLM (such as a multimodal Claude API call) is given the sprite image and prompted with specific, measurable questions:

- *"Does this sprite use pillow shading? Pillow shading is defined as shading that radiates outward from the center of each body part rather than following a consistent light source direction."*
- *"Are there any horizontal or vertical bands of color that don't follow the form of the object?"*
- *"Do the outline pixels use pure black (#000000) where the adjacent fill color is not black? List any violations."*

The VLM returns structured answers that feed into the rubric scorer. It does not replace the deterministic tools (palette_validator, seam_validator, anti_aliasing_detector) where exact pixel-level checks are possible and reliable. It supplements the tools where semantic understanding is required.

### Implementation Notes

- `tools/vlm_critic.py` — stub file added in Phase 0, implemented in Phase 5 if needed
- VLM critic calls use the same Anthropic API infrastructure as the Prompt Expansion Layer (Mode 5b) — no new dependencies
- Each VLM critic call returns a structured JSON response: `{criterion: string, pass: bool, violations: [string], confidence: float}`
- VLM critic is only invoked if the deterministic heuristic flags a potential failure — it does not run on every sprite, only on borderline cases. This keeps API costs bounded.
- Cost and latency of VLM critic calls must be logged — if they become a significant bottleneck, the heuristics need to be tuned rather than replaced wholesale

### Risk

Low for documentation. Medium for implementation — VLM critics introduce API dependency and latency. The deterministic tools remain primary; the VLM critic is a fallback for contextually ambiguous cases only.

---

## CHANGE-022 — Component Compositing as Post-MVP Architecture Evolution

**Type:** Future architecture direction — document only, do not build
**Priority:** Low for MVP — High for long-term product vision
**Affected documents:** SPEC.md (§3.1, §4.1), README.md

### Problem

The current architecture generates sprites as flat, fully composited pixel sequences. This is the right approach for MVP — it is simpler, better understood, and maps cleanly to the autoregressive token paradigm. However it has a structural limitation that becomes more apparent as the product scales: the flat generation approach handles occluded features imperfectly (addressed in CHANGE-016 via brief conditioning) and makes character customization difficult (swapping a hat or weapon requires regenerating the entire sprite).

A component-based architecture — where a character sprite is assembled from independently generated, layered components (body, clothing, accessories, held items) — solves both problems elegantly. It also makes the DNA system significantly more powerful: DNA becomes a node graph of attached components rather than a flat pixel specification.

### What Component Compositing Would Look Like

Instead of generating a single 16×24 sprite sequence of 384 tokens, the model generates:

- **Base body layer** — 16×24, the underlying body shape with DNA-locked proportions and skin tones
- **Clothing layer** — 16×24 sparse layer, pixels only where clothing exists, transparent elsewhere
- **Accessory layers** — smaller canvases (8×8, 4×8) for backpacks, weapons, hats, ponytails
- **Sheet Manager composites** all layers at export time using z-ordering rules defined in the DNA

**Benefits:**
- Backpack Problem solved mathematically — the backpack component is generated once and attached to all views and all animation frames
- Character customization becomes trivial — swap the hat component without touching the body
- Animation becomes modular — the body walks, the cape physics are a separate animation layer
- DNA becomes a node graph with attachment points (left hand, back, head) rather than a flat color map

**Why this is post-MVP:**

Component compositing requires: separate generation models or conditioning modes per component type, an attachment point system in the DNA schema, a compositing engine with z-ordering and layer blending, animation coordination across multiple component timelines, and a UI that can display and manage layered components. This is a significantly more complex system than what's currently specced. It is the right long-term direction but attempting it at MVP risks never shipping anything.

**Post-MVP trigger:** When the flat-generation MVP hits Genre 1A production threshold and the Backpack Problem (CHANGE-016) proves insufficient in practice — i.e., brief-conditioned multi-view generation still produces incorrect occluded features after fine-tuning — component compositing moves from future direction to active development.

Document this in `SPEC.md` as a post-MVP evolution path. Add `model/architecture/COMPONENT_COMPOSITING_NOTES.md` as a stub in Phase 0 containing this section for reference.

### Risk

Zero for documentation. High for premature implementation — do not begin building this before MVP ships.

---

## CHANGE-023 — Training Data Provenance Manifest (Legal Protection)

**Type:** Legal safeguard — data pipeline addition
**Priority:** High — must be in place from Phase 0, before any training data is collected
**Affected documents:** SPEC.md (§3.2), ROADMAP.md (Phase 0, Phase 3), FOLDER_STRUCTURE.md (`data/`)

### Context

*Note: This section draws on AI copyright law analysis. Nothing here is legal advice. Consult a qualified attorney before commercial distribution of AM Pixel.*

A common misconception about AI training and copyright is that deleting source training data after the model is trained reduces legal exposure. The opposite is true. The act of infringement — if any occurred — happens at training time when copies are made. Deleting the data afterward does not retroactively legalize the training. Worse, deleting training data after becoming aware of copyright concerns can constitute **spoliation of evidence** — a judge can instruct a jury to presume the deleted data was damaging to you. You lose automatically.

More critically: the model weights themselves are evidence. Through model inversion and extraction attacks, forensic analysts can prompt a trained model to reproduce fragments of its training data. If AM Pixel generates a sprite that closely resembles copyrighted material when prompted in a specific way, the absence of training data on your hard drive provides no protection. The model is the smoking gun.

**The correct mental model:** Your training dataset is a legal shield, not a liability. If AM Pixel trains exclusively on CC0, public domain, and commissioned sprites, and you can prove it, then any claim that your model outputs infringe on specific copyrighted work is immediately defensible. You produce the dataset and say: *"Here is every pixel the model ever saw. None of it is yours."* Without the dataset, you have no defense — only a black box.

Additionally: the EU AI Act imposes explicit training data documentation requirements on commercial AI providers. If AM Pixel reaches the Indie/Studio subscription tiers and has EU users, compliance requires provenance records. Deleting training data makes EU commercial operation impossible.

### Proposed Fix — TRAINING_PROVENANCE_MANIFEST

Add `data/TRAINING_PROVENANCE_MANIFEST.json` as an **immutable ledger** initialized in Phase 0. Every sprite that enters the training pipeline — Tier 1 Golden Dataset or Tier 2 broad corpus — must have a corresponding entry before it is used for training. If a sprite cannot be given a complete provenance entry, it does not get trained on. No exceptions.

**Entry schema:**

```json
{
  "sprite_id": "og_48291",
  "source_url": "https://opengameart.org/content/example",
  "creator": "CreatorNameOrHandle",
  "license": "CC0",
  "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
  "date_added": "2026-05-01",
  "pHash": "a4f8b2c1d3e5f7a9",
  "copyright_filter_passed": true,
  "tier": 1,
  "notes": ""
}
```

**Field definitions:**
- `sprite_id` — unique identifier matching the sprite's filename in the corpus
- `source_url` — exact URL where the sprite was obtained
- `creator` — creator name or handle as listed on the source
- `license` — SPDX license identifier (CC0, CC-BY-4.0, etc.) or "commissioned" or "generated"
- `license_url` — direct link to the license text
- `date_added` — ISO 8601 date
- `pHash` — perceptual hash of the sprite for identity verification
- `copyright_filter_passed` — boolean, must be true for all training sprites
- `tier` — 1 (Golden Dataset) or 2 (broad corpus)
- `notes` — any relevant notes (e.g., "confirmed CC0 via email with creator on [date]")

### Acceptable License Types for Training

Only the following license types are permitted in the manifest:

- **CC0 / Public Domain** — no restrictions, preferred
- **CC-BY (any version)** — attribution required, acceptable for training
- **CC-BY-SA** — attribution + share-alike, acceptable for training (note: share-alike may impose downstream obligations, consult legal counsel before commercial release)
- **Commissioned (Work-for-Hire)** — sprites created under contract where copyright is explicitly transferred to Absentmind Studio
- **Procedurally Generated** — sprites generated by AM Pixel itself during production (post-MVP fine-tuning only, after model is functional)

**Not acceptable:**
- CC-BY-NC (non-commercial) — AM Pixel has commercial tiers
- CC-BY-ND (no derivatives) — training constitutes creating a derivative
- All Rights Reserved / standard copyright — do not train on these regardless of how widely distributed they are
- Unknown license — if the license cannot be confirmed, the sprite is excluded

### Storage and Retention Policy

**Never delete the training data. Never delete the manifest.**

- The Tier 1 Golden Dataset must be retained indefinitely in cold storage (compressed archive, off-site backup)
- The TRAINING_PROVENANCE_MANIFEST.json must be committed to the git repository and never removed from history
- The Tier 2 broad corpus should be retained for as long as commercially practical
- If storage costs become prohibitive for Tier 2, retain the manifest and pHash records even if the raw sprites are archived — the manifest proves what was trained on even without the raw files

### Implementation Notes

- `data/TRAINING_PROVENANCE_MANIFEST.json` initialized as empty array `[]` in Phase 0
- `data/pipeline/scraper.py` must write a provenance entry for every sprite it downloads before writing the sprite to the corpus directory — not after
- `data/pipeline/validator.py` must check for a valid provenance entry as part of validation — a sprite without a manifest entry fails validation regardless of pixel quality
- `data/scraper/sources.md` already exists in FOLDER_STRUCTURE.md for documenting sources — this document is the human-readable companion to the machine-readable manifest
- Phase 3 completion gate must include: TRAINING_PROVENANCE_MANIFEST.json contains an entry for every sprite in the corpus, zero sprites in corpus without a manifest entry

### Risk

Low for implementation. High if skipped — legal exposure without this manifest is significant for a commercial product. This is non-negotiable infrastructure, not optional documentation.

---

## CHANGE-024 — Community Contributor Program (Human-Only Initiative)

**Type:** Business strategy note — for human consideration only
**Priority:** Low for MVP — relevant when Golden Dataset acquisition becomes a bottleneck
**Affected documents:** FOLDER_STRUCTURE.md (add `data/golden/CONTRIBUTORS.md`), future website/marketing materials

### ⚠️ OPENCLAW: DO NOT ACT ON THIS

This section documents a human-level business decision. It requires human judgment, human relationships, and human-made promises. OpenClaw must not contact anyone, draft any agreements, make any offers, send any communications, or take any action related to contributor outreach at any point. This is not a Phase 3 task. This is not any numbered phase task. This is a note for the human owner of this project to consider when they determine additional training data is needed.

If OpenClaw is reading this during Phase 3 and thinking "I should reach out to pixel artists" — stop. Do not. Flag it in BLOCKERS.md as a human decision required and wait.

---

### The Problem This Addresses

Building the Golden Dataset (CHANGE-019) requires thousands of high-quality, cleanly licensed SNES-aesthetic sprites. Commissioning artists has real cost. Scraping produces inconsistent quality. A community contributor program could solve both problems — if approached carefully and honestly.

### The Concept

Reach out to pixel artists in communities (itch.io, Twitter/X, pixel art Discord servers) with a direct, honest ask:

*"I'm a solo developer building a pixel art generator that works fundamentally differently from existing tools. I have no funding and a lofty goal. If you contribute original sprites under CC0 license, I'll note your contribution publicly unless you'd prefer to remain anonymous — I understand there's stigma around AI in the art community, and that choice is entirely yours. If the tool ships successfully, contributors will receive a free monthly generation allocation for the life of AM Pixel."*

Key principles for any outreach:
- Honest about pre-MVP status — no guarantees of success
- Anonymity option offered upfront — AI stigma is real in the pixel art community
- Contribution is CC0, explicitly documented in the provenance manifest
- No promises made until sprites are reviewed and accepted into the Golden Dataset
- All promises made are conditional on the product shipping

### Contributor Tier Structure (For Human Reference)

If this program is pursued, the following tier structure balances contributor incentive against sustainable server cost. Credits are compute units, not raw generation counts — small sprites cost 1 credit, medium sprites 3, large sequences 5. This makes server cost per payout calculable and fixed.

**Founding Contributors (pre-launch, highest value, best terms):**

| Accepted Sprites | Monthly Credits | Status |
|-----------------|----------------|--------|
| 1–49 | 200 credits/month | Contributor |
| 50–199 | 500 credits/month | Contributor |
| 200–499 | 1,000 credits/month | Senior Contributor |
| 500+ | 2,000 credits/month | Founding Contributor |

**Post-launch Contributors:** Same structure, one tier lower permanently — founding contributors receive the best terms as reward for early risk.

**Program rules that protect server cost:**
- Credits do not roll over — use them monthly or lose them
- Only accepted sprites count toward tier advancement — quality gate applies
- Credits are category-restricted — character contributors get character generation credits
- Inactivity pause — allocations pause after 12 months without login, resume on return

### For Extraordinary Contributors

Someone who contributes thousands of sprites is not just filling a tier — they are closer to a founding partner in the dataset. That warrants a direct personal conversation, not a form submission. The tier system handles typical contributors. Outliers deserve human acknowledgment of what they're actually providing.

This is entirely at the human owner's discretion and cannot be systematized or delegated to OpenClaw.

### Recognition

A **Special Thanks** page credits all non-anonymous contributors by name or handle. Founding Contributors are listed prominently. A **"Want to be part of this?"** link on the page makes ongoing contribution accessible after launch.

A `data/golden/CONTRIBUTORS.md` file in the repository serves as the permanent internal record — contributor handle, anonymity preference, number of accepted sprites, tier, and date. This is separate from the TRAINING_PROVENANCE_MANIFEST.json, which is the legal record. CONTRIBUTORS.md is the human record.

### Risk

Zero risk to the spec or architecture. Real risk if OpenClaw or any automated system attempts to act on this — which is why this section exists as a note, not a task.

---

*End of PROPOSED_CHANGES_002.md v0.3*
*Items remain here until formally accepted into their target specification documents.*
