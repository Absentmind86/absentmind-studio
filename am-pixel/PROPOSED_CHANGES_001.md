# AM Pixel — Proposed Changes & Additions
**Working Document | Version 0.1**

This document tracks proposed changes, refinements, and additions to the AM Pixel specification. It is not a replacement for any existing document. It is a staging area. Items here are under discussion and have not been committed to any spec file. Each item includes the rationale, the affected documents, and the proposed implementation.

---

## CHANGE-001 — Structure-Aware Generation Order

**Type:** Core architecture refinement
**Priority:** High — affects training pipeline and model architecture
**Affected documents:** SPEC.md (§3.1, §3.2), ROADMAP.md (Phase 3, Phase 4)

### Problem

The current AR transformer specification generates tokens in raster order — left-to-right, top-to-bottom, like reading a book. This is arbitrary relative to how pixel art is actually constructed. A raster-order model must commit to top-left pixels before it has any global understanding of what the full sprite will look like. This creates a compounding problem: early token decisions constrain later ones in ways that can produce misaligned proportions, broken outlines, and incoherent shading — particularly at small sprite sizes where every pixel carries significant weight.

### Proposed Solution

During training data preparation (Phase 3), reorder each sprite's token sequence from raster order into structure-aware order:

1. **Outline pixels first** — the single-pixel border defining the silhouette
2. **Base fill pixels second** — large flat color regions (body, clothing, skin)
3. **Shading pixels third** — shadow and highlight ramps applied to base fills
4. **Detail pixels last** — small features, accessories, face details, embroidery

The transformer architecture itself does not change. The training objective (next-token prediction) does not change. Only the ordering of tokens in training sequences changes. At inference time, the model generates in the same learned order — outline, fill, shade, detail — which mirrors the intentional construction process of a professional pixel artist.

### Implementation Notes

- The sprite extraction pipeline (Phase 3) must be extended with a pixel classification step that assigns each pixel to one of the four structural categories above
- Classification can be rule-based: outline pixels are those adjacent to the transparent background; fill pixels are large contiguous regions of a single palette index; shading pixels are non-outline pixels whose palette index belongs to a shadow or highlight ramp; detail pixels are everything remaining
- The palette index sequence stored for each training example is reordered accordingly, with a positional encoding that preserves the original (x, y) canvas coordinates so the model can reconstruct spatial position
- The DNA conditioning tokens remain unchanged — they are prepended before the reordered sequence as currently specified
- This change adds complexity to the data pipeline but zero complexity to the model architecture

### Risk

Low. This is a training data ordering decision, not an architectural change. If structure-aware ordering does not produce measurable improvement over raster order by Phase 5 (Practice Gauntlet), the ordering can be reverted to raster without any model changes. The comparison should be documented as a Phase 4 experiment.

---

## CHANGE-002 — Prompt Expansion Layer

**Type:** New feature addition
**Priority:** Medium — improves output quality and user experience, not required for MVP
**Affected documents:** SPEC.md (§3.3 system components table, §14 web UI), ROADMAP.md (Phase 7)

### Problem

The AM Pixel DNA system is only as good as its inputs. A user who types "old wizard" produces a thin, underspecified brief that the generation engine must interpret with minimal guidance. The model fills the gaps with statistical defaults — which produces generic output that lacks the specific personality and visual anchors that make pixel art characters memorable. Users who don't know what they want, or don't know how to describe it, are penalized for their uncertainty.

### Proposed Solution

Add a **Prompt Expansion Layer** as an optional step in the character creation conversation flow. Before generation begins, the user can trigger expansion of their short description into a fully detailed character brief. This brief then populates the DNA `brief` fields and serves as the richest possible conditioning input for generation.

**User flow:**

1. User opens chat, selects "New Character"
2. User types a short description: *"old wizard"*
3. User clicks **Expand** button (or types /expand)
4. The system sends the short description to a language model with a structured expansion prompt
5. The expansion is returned and displayed to the user in an editable text area, pre-filling the DNA brief fields:
   - `personality`
   - `role`
   - `defining_trait`
   - Visual anchors (clothing, accessories, color associations, posture, expression)
6. User edits the expansion freely before confirming
7. Confirmed expansion becomes the brief that feeds generation

**Example expansion:**

Input: *"old wizard"*

Output:
> An elderly male wizard, deeply stooped from decades hunched over spell books. Long silver beard with a slight yellow tinge at the tips. Midnight blue pointed robe, fraying at the hem, faded gold star embroidery barely visible. Worn leather belt with a cracked potion vial glowing amber at the hip. Skeletal hands with prominent knuckles, ink-stained fingertips. Deep-set eyes under heavy brows — wise but perpetually exhausted. Gnarled oak staff, twisted asymmetrically, topped with a cloudy crystal that pulses faintly. Moves slowly, deliberate. The impression of someone who has seen everything twice and is no longer impressed.

### Implementation Notes

- The expansion call is a standard Claude API call with a system prompt that knows the DNA schema structure and is instructed to output content formatted for the `brief` fields
- The system prompt should also be aware of the project's GENRE_TAXONOMY and active style bible (SNES aesthetic, palette feel) so expansions are genre-appropriate
- The expansion is **always editable** before confirmation — it is a suggestion, not a decision
- The expansion is **optional** — users who know exactly what they want skip it entirely
- Freeform Mode 7 does not use the expansion layer (no DNA, no brief)
- The Expand button lives in the chat input area of the web UI — visible only when the active mode is a character or NPC generation mode
- This feature does not require a new system component — it is a capability of the existing Approval Pipeline component (§3.3). The system components table should be updated to note that the Approval Pipeline includes prompt expansion.

### Phase Placement

This feature can be built during Phase 7 (Production Pipeline Integration) without blocking earlier phases. It is not required for the Practice Gauntlet. It should be included in the end-to-end test in Phase 7.

### Risk

Very low. It is a single API call with a structured prompt. The only failure mode is a poor expansion that the user corrects before confirming. The generation pipeline is unchanged.

---

---

## CHANGE-003 — GPU Backend Universalization

**Type:** Core architecture fix
**Priority:** High — current CUDA-only requirement cuts out AMD, Apple Silicon, and CPU-only users
**Affected documents:** SPEC.md (§3.1, §15), ROADMAP.md (Phase 0, Phase 4), OPENCLAW_PROMPT.md, FOLDER_STRUCTURE.md

### Problem

Every hardware reference in the current documents hardcodes NVIDIA + CUDA as a requirement. This is unnecessarily restrictive. PyTorch already abstracts hardware through its device system. Hardcoding CUDA means anyone on AMD, Apple Silicon (M1/M2/M3), or a CPU-only machine cannot run the tool at all — which eliminates a large portion of indie developers, who are exactly the target audience.

### Proposed Solution

Replace all CUDA-specific hardware requirements with a detection hierarchy. At startup, the system detects available hardware and selects the optimal backend automatically:

1. **NVIDIA GPU detected** → CUDA (fastest, preferred for training)
2. **AMD GPU detected** → ROCm (PyTorch-supported, nearly equivalent performance)
3. **Apple Silicon detected** → MPS — Metal Performance Shaders (PyTorch supports M1/M2/M3)
4. **Other GPU detected** → attempt OpenCL via PyTorch extensions
5. **No GPU / fallback** → CPU (inference is usable; training is slow but functional)

Instead of `device = "cuda"` hardcoded throughout, all device references route through a detection utility that returns the best available device. This is a small code change with large accessibility impact.

### Document-Level Changes Required

**SPEC.md §3.1:**
Remove: *"Hardware target: NVIDIA GPU with CUDA, minimum 10GB VRAM"*
Replace with: the full detection hierarchy above, with a note that training time varies significantly by tier (minutes on CUDA/ROCm, hours on CPU)

**SPEC.md §15 Technical Stack:**
Rewrite the hardware bullet entirely. Add the detection priority list. Add a note that cloud GPU rental (RunPod, Vast.ai, Lambda Labs) is recommended for training-only runs on CPU machines — inference does not require it.

**ROADMAP.md Phase 0:**
Remove the current gate condition that halts if CUDA is not found.
Replace with: "Detect available hardware, log GPU model and backend selected, write result to `logs/hardware.log`. Proceed on any hardware tier."
Phase 4 training section: add a note that training time estimates vary by hardware tier and should be documented during the training run.

**OPENCLAW_PROMPT.md:**
Remove the CUDA-only hardware context section.
Replace with a directive: detect hardware at startup, log the result, select optimal backend, proceed. Do not halt on non-CUDA hardware.

**FOLDER_STRUCTURE.md:**
Add `model/hardware/detector.py` to the Phase 0 required tooling list. This utility is responsible for hardware detection and device selection and must be built and validated before any training work begins.

### Risk

Low. PyTorch's device abstraction handles the heavy lifting. The main implementation concern is ensuring training scripts don't contain any hardcoded `"cuda"` strings — a straightforward audit task for Phase 0.

---

## CHANGE-004 — SPEC.md Structural Fixes (Missing Header + Section Numbering Gap)

**Type:** Document correction
**Priority:** High — structural errors in the primary spec document create confusion for OpenClaw
**Affected documents:** SPEC.md

### Problem

Two structural errors exist in SPEC.md:

**Problem 1 — Missing Section 6 header:**
The heading `## 6. Project Organization` is completely absent. Subsections 6.1, 6.2, and 6.3 exist in the document but are orphaned — they appear under no parent heading. This was lost during a previous edit. OpenClaw reading the document will encounter numbered subsections with no parent, which creates ambiguity about document structure.

**Problem 2 — Missing Section 13:**
Section 13 was never created. The original spec had Technical Stack at section 13. When Web UI was added as section 14, Technical Stack became 15, but nothing was placed at 13. The document jumps from section 12 directly to section 14, leaving a visible gap. This is a counting error that could cause OpenClaw to search for a section that doesn't exist.

### Proposed Fix

1. Restore the `## 6. Project Organization` heading immediately above subsection 6.1 in SPEC.md
2. Either: create a legitimate section 13 for content that belongs there (if any is identified), or renumber — collapse the gap so sections run 12 → 13 (Web UI, currently labeled 14) → 14 (Technical Stack, currently labeled 15) with no skip

Option 2 (renumber cleanly) is preferred unless a real content gap justifies a new section 13.

### Risk

Very low. These are formatting corrections with no impact on content or logic.

---

## CHANGE-005 — OPENCLAW_PROMPT Fixes (Document List + Forced Confirmation)

**Type:** Document correction + behavioral safeguard
**Priority:** High — affects how OpenClaw initializes and what it reads before starting
**Affected documents:** OPENCLAW_PROMPT.md

### Problem 1 — Brittle Document Count

The OPENCLAW_PROMPT currently instructs OpenClaw to read "four specific documents" before starting. This number is already wrong — the correct count is five documents (root README, SPEC, ROADMAP, GENRE_TAXONOMY, FOLDER_STRUCTURE), with the prompt itself being the sixth document OpenClaw is already holding. More importantly, any future document addition will silently make the count wrong again without anyone noticing.

### Fix 1

Remove the count entirely. Replace with an explicit named list:

> *"Before beginning Phase 0, read each of the following documents completely, in this order: root README.md, am-pixel/SPEC.md, am-pixel/ROADMAP.md, am-pixel/GENRE_TAXONOMY.md, am-pixel/FOLDER_STRUCTURE.md."*

Named lists don't go stale. Counts do.

### Problem 2 — Missing Forced Confirmation Paragraph

The prompt does not currently require OpenClaw to confirm its understanding of critical definitions before proceeding. The two-threshold system (individual 95/100 score vs. 99/100 batch pass rate) is the single most important concept in the entire project and is defined in three separate documents. If OpenClaw misreads it once, every phase gate evaluation is wrong.

### Fix 2

Add a forced confirmation requirement to the prompt. Before OpenClaw begins any Phase 0 task, it must output a written confirmation that demonstrates it has correctly understood the distinction between the two thresholds — what each measures, and how they differ. If OpenClaw cannot state this correctly, it must re-read the relevant sections before proceeding.

### Risk

Very low. Both fixes are additive or clarifying. Neither removes existing functionality.

---

## CHANGE-006 — Folder Structure Additions

**Type:** Structural addition
**Priority:** Medium — organizational completeness
**Affected documents:** FOLDER_STRUCTURE.md

### Items to Add

**1. `am-pixel/README.md` — intra-folder hub**
The root README explains the overall project. But a developer navigating directly into the `am-pixel/` directory has no orientation document — they land in a folder full of spec files with no entry point. A short README inside `am-pixel/` that describes what the folder contains and points to each document solves this. This is especially important for OpenClaw, which may navigate the repo non-linearly.

**2. Initialized empty log files in `logs/`**
The `logs/` directory should be initialized with empty placeholder files for each expected log type so the directory structure is committed to git from Phase 0. An empty directory is not tracked by git and will disappear. Placeholder files (e.g., `hardware.log`, `training.log`, `evaluation.log`, `errors.log`) with a single comment line ensure the structure exists from the first commit.

**3. `model/hardware/detector.py`**
As described in CHANGE-003 — the hardware detection utility belongs in `model/hardware/` and must be listed in FOLDER_STRUCTURE.md as a Phase 0 required tool. It is built and validated during Phase 0 before any training work begins.

### Risk

Very low. All additions. Nothing removed or renamed.

---

---

## REFINEMENT-001A — Transparent Pixel Category (Addition to CHANGE-001)

**Affects:** CHANGE-001 (Structure-Aware Generation Order)

The four-category pixel classification in CHANGE-001 (outline, fill, shade, detail) is missing a fifth implicit category: **transparent pixels**. Most sprites have significant transparent areas defining the alpha mask — the background void around the character. If transparent pixels are not classified and ordered explicitly, the model may bleed palette tokens into empty space during long rollouts.

**Proposed addition to CHANGE-001:** Transparent pixels are classified as a fifth category and generated first — before outline pixels — so the model commits to the full alpha mask before any visible content is placed. This gives the model a hard spatial boundary from token one.

Additionally: the data pipeline should log the distribution of all five pixel categories across the training corpus (e.g., what percentage of tokens are transparent, outline, fill, shade, detail on average). If any category is severely underrepresented it will cause generation failures and should be caught before training begins, not after.

---

## REFINEMENT-002A — Style-Bible Guardrails in Expansion Prompt (Addition to CHANGE-002)

**Affects:** CHANGE-002 (Prompt Expansion Layer)

The expansion layer system prompt must explicitly forbid anachronistic and non-SNES-appropriate details. Without this, the expansion model will naturally drift toward modern aesthetics — glowing neon, cyberpunk elements, hyper-detailed accessories, gradients — that are incompatible with the style bible and will produce unworkable generation inputs.

**Proposed addition to CHANGE-002:** The expansion layer system prompt must include explicit negative constraints aligned with the SNES style bible: no glowing effects, no gradients, no modern materials, no sub-pixel detail that couldn't survive at 1× scale, palette color count awareness. The expansion should describe a character that a SNES-era studio could have actually shipped.

---

## REFINEMENT-003A — Inference Speed Test in Hardware Log (Addition to CHANGE-003)

**Affects:** CHANGE-003 (GPU Backend Universalization)

The hardware detection utility should do more than log GPU model and backend selected. It should also run a quick baseline inference test — generate one small test sprite (e.g., 16×16) and log tokens per second. This gives the user an immediate, concrete sense of how long training and inference will actually take on their specific hardware before they commit to a multi-hour training run.

**Proposed addition to CHANGE-003:** After backend selection, `detector.py` runs a lightweight inference benchmark and writes the result to `logs/hardware.log` alongside GPU model, VRAM, and backend. Example output: `"Backend: ROCm | GPU: RX 7900 XTX | VRAM: 24GB | Baseline inference: 42 tokens/sec"`.

---

## REFINEMENT-005A — Diffusion/RGB Architecture Confirmation (Addition to CHANGE-005)

**Affects:** CHANGE-005 (OPENCLAW_PROMPT Fixes)

The forced confirmation paragraph in CHANGE-005 currently covers the two-threshold distinction. It should also include an explicit architecture confirmation to prevent OpenClaw from introducing diffusion components, RGB pipelines, or 3D-to-pixel stages in any phase — even if a web search during Boot Training surfaces compelling-looking research using those approaches.

**Proposed addition to CHANGE-005:** The forced confirmation must include: *"Confirm that you understand this project will never use diffusion models, 3D-to-pixel pipelines, RGB image generation, or any approach that generates in continuous color space at any stage. All generation is discrete palette-index token prediction from first token to last."*

---

## CHANGE-007 — Sequence Length & Error Accumulation Mitigation

**Type:** Core architecture risk — requires explicit design decision before Phase 4
**Priority:** High — this is the single largest technical risk in the current spec
**Affected documents:** SPEC.md (§3.1, §3.3), ROADMAP.md (Phase 4)

### Problem

The current spec defines generation as a flat raster-order sequence of palette-index tokens. A 16×24 world sprite is 384 tokens — manageable. A 48×64 battle sprite is 3,072 tokens. At that length, autoregressive models accumulate prediction errors compoundingly: the model does well on the first 30–40% of the sequence, then errors from earlier tokens propagate and the bottom/right portion of the sprite degrades into anatomical inconsistency or palette drift. This is a documented failure mode in every pixel-level autoregressive model from PixelCNN onward. The 95/100 per-sprite and 99/100 batch thresholds will be very difficult to hit consistently at battle-sprite scale without explicit mitigation.

The current spec does not address this problem.

### Decision Required Before Phase 4

Three mitigations exist, each with different implementation cost. A decision must be made before the transformer architecture is built — this cannot be retrofitted cleanly.

**Option A — Hierarchical / multi-scale generation (VAR-style):**
Generate a coarse low-resolution palette grid first (e.g., 6×8 for a 48×64 sprite at 8× downscale), then autoregressively refine at progressively higher resolutions, conditioning each scale on the previous scale's output plus the DNA. This slashes effective sequence length per step and gives the model global structure before committing to fine detail. Architecturally more complex but has the strongest theoretical basis for long-sequence coherence.

**Option B — Structure-aware generation order (CHANGE-001, already proposed):**
Generating outline → fill → shade → detail already partially mitigates the problem by front-loading the most structurally important tokens. The model "knows" the full silhouette before placing any detail. This is lower-complexity and may be sufficient for the sprite sizes in scope — but is an incomplete fix for sequences above ~1,500 tokens.

**Option C — Accept the risk and address it empirically in Phase 4:**
Build the flat raster transformer as specified, evaluate failure patterns at battle-sprite scale during the Practice Gauntlet, and add hierarchical generation in Phase 6 if the 99/100 threshold cannot be hit without it. Lowest upfront cost, highest risk of Phase 6 being a near-full rebuild of the generation architecture.

### Recommendation

Option B (already in CHANGE-001) as the immediate low-cost mitigation, with Option A explicitly scheduled as a Phase 4 architectural experiment — not deferred indefinitely. The ROADMAP should include a specific gate in Phase 4: evaluate flat-sequence performance on battle sprites at 48×64 and above. If pass rate falls below 70% on sequences over 1,500 tokens, implement hierarchical generation before proceeding to Phase 5.

---

## CHANGE-008 — DNA Conditioning Architecture Decision

**Type:** Core architecture decision — must be made before Phase 4
**Priority:** High — affects transformer implementation directly
**Affected documents:** SPEC.md (§3.1, §4)

### Problem

The current spec conditions generation by prepending DNA JSON as context tokens at the start of the sequence. For short sequences (16×24 = 384 tokens) this works well — the DNA conditioning remains in the attention window and strongly influences all token predictions. For longer sequences (48×64 = 3,072 tokens), the attention mechanism must span thousands of tokens back to the DNA prefix. In practice, the conditioning signal weakens — later tokens in the sequence are less tightly constrained by the DNA than earlier ones. This means a battle sprite's lower body is less DNA-locked than its head and shoulders.

### Two Approaches

**Approach A — DNA prefix (current spec):**
Simple, proven, works well at short sequence lengths. Lower implementation complexity. May require stronger training signals (more high-quality battle sprites) to compensate for signal dilution at long range.

**Approach B — DNA as cross-attention embeddings:**
The DNA JSON is encoded into a fixed set of learned conditioning vectors that attend to every token prediction step via dedicated cross-attention layers in the transformer. The DNA signal is equally strong at token 1 and token 3,072. Architecturally more complex — requires adding cross-attention heads — but eliminates conditioning dilution entirely.

### Recommendation

This is a genuine architectural fork. Approach A is the right starting point — implement it, measure conditioning strength empirically during Phase 4 by comparing DNA consistency scores between early and late tokens in long-sequence sprites. If late-token DNA drift is measurable and consistent, upgrade to Approach B in Phase 6. Do not build cross-attention from the start without evidence it is needed — unnecessary complexity before the simple version has been tested is the wrong order of operations.

Add a specific Phase 4 measurement task: after initial training, generate 20 battle sprites and run DNA consistency checks separately on the top half vs. bottom half of each sprite. Document the delta. If bottom-half consistency is more than 10% lower than top-half, Approach B becomes the Phase 6 priority.

---

## CHANGE-009 — Animation Temporal Coherence (Explicit Gap Documentation)

**Type:** Known gap — explicit documentation and phase placement
**Priority:** Medium — will not block Phase 0–7, will surface in Phase 8 production validation
**Affected documents:** SPEC.md (§5, animation sections), ROADMAP.md (Phase 7, Phase 8)

### Problem

The current spec generates each animation frame independently, conditioned only on the shared DNA. This enforces character continuity (same colors, same proportions, same palette) but not motion continuity. A walk cycle generated frame-by-frame will have consistent character identity but may have inconsistent weight, timing, and pose-to-pose flow. Frames may not read as a coherent motion sequence — they will look like the same character drawn multiple times rather than the same character in motion.

This gap is partially acknowledged in the spec but is not explicitly scoped, phased, or designed around.

### Proposed Resolution

Document this gap explicitly in SPEC.md with a clear statement of what is and isn't solved by the DNA system alone. Add a Phase 7 or Phase 8 stretch task: evaluate whether frame-independent generation with DNA conditioning is sufficient for walk cycles at the 95/100 rubric threshold. If walk cycles fail the rubric for motion quality rather than character quality, a lightweight temporal conditioning head is the solution — the next frame is conditioned on the previous frame's tokens plus the shared DNA. This stays fully within the discrete palette-index token world.

Do not build temporal conditioning speculatively. Build it if and when frame-independent generation demonstrably fails the motion quality criteria of the rubric.

---

*End of PROPOSED_CHANGES_001.md v0.1*
*Items remain here until formally accepted into their target specification documents.*