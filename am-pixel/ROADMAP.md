# AM Pixel — Execution Roadmap
**Absentmind Studio | Version 1.4**

---

## How To Read This Document

This roadmap defines every phase of AM Pixel development from system initialization to production-ready tool. Each phase has explicit completion gates — measurable criteria that must all be true before advancing. OpenClaw does not advance phases on its own judgment. It advances phases when gate criteria are objectively met.

If a gate criterion cannot be met, OpenClaw halts, documents the specific blocker, and waits for human input before proceeding.

---

### ⚠️ CRITICAL DEFINITION — TWO DIFFERENT THRESHOLDS

This document references two thresholds. They measure completely different things.

**95/100 — Individual sprite score.**
Each sprite is evaluated on the rubric. It must earn 95 points or higher out of 100 to pass. This applies to every single sprite generated throughout the entire project.

**99/100 production threshold — Batch pass rate. NOT a score of 99 points.**
This means: in a validation batch of 100 generated sprites, at least 99 of those individual sprites must each independently score 95 or above on the rubric. This measures the model's overall reliability before advancing a phase or genre.

- 99 sprites each scoring 95+ → BATCH THRESHOLD MET ✅
- 1 sprite scoring 99 points → BATCH THRESHOLD NOT MET ❌ (only 1 sprite, need 99 out of 100 passing)
- 98 sprites all scoring 100 points → BATCH THRESHOLD NOT MET ❌ (98 pass, minimum is 99)

Every time this document says "99/100 threshold" it means this batch pass rate. It never refers to a point score of 99.

---

## Phase 0 — System Initialization
*Initialize environment, verify hardware, establish project structure*

### Tasks
- [ ] Run hardware detection via `model/hardware/detector.py` — detect available GPU/backend, log result to `logs/hardware.log`. Proceed on ANY hardware tier. Do NOT halt if CUDA is unavailable.
  - Detection hierarchy: NVIDIA→CUDA, AMD→ROCm, Apple Silicon→MPS, other GPU→OpenCL, no GPU→CPU
  - Log: GPU model, VRAM, backend selected, baseline inference speed (tokens/sec on a 16×16 test sprite)
- [ ] Verify PyTorch installation functional on detected backend
- [ ] Initialize full folder structure per `FOLDER_STRUCTURE.md`
- [ ] Initialize git repo (or connect to existing GitHub repo)
- [ ] Install all required Python dependencies — log versions
- [ ] Verify disk space — minimum 100GB available for training data and model checkpoints
- [ ] Build all required tooling scripts (palette_validator, dna_diff, rubric_scorer, sheet_manager, seam_validator, layer_compositor, effect_timing_evaluator, icon_grammar_checker, etc.)
- [ ] Initialize `tools/vlm_critic.py` stub — documented interface only, not implemented (CHANGE-021)
- [ ] Initialize `data/pipeline/pose_extractor.py` stub — documented interface only, not implemented (CHANGE-015)
- [ ] Initialize `model/architecture/COMPONENT_COMPOSITING_NOTES.md` — post-MVP architecture reference (CHANGE-022)
- [ ] Initialize `data/TRAINING_PROVENANCE_MANIFEST.json` as empty array `[]` — immutable legal ledger, never deleted (CHANGE-023)
- [ ] Initialize `data/golden/` directory and `data/golden/CONTRIBUTORS.md` placeholder
- [ ] Audit all training and inference scripts — confirm zero hardcoded `"cuda"` strings; all device references must route through `model/hardware/detector.py`
- [ ] Create `pipeline/modes/mode7_freeform.py` stub with documented interface
- [ ] Initialize `ui/` directory — build working web UI skeleton: chat panel, 1×/4× image preview, approve/reject/adjust controls, project tabs, freeform tab. Must be functional before Phase 5.
- [ ] Initialize empty log placeholder files in `logs/` (hardware.log, training.log, evaluation.log, generation_log.md, rebuild_log.md, errors.log, BLOCKERS.md, phase_gates.md)
- [ ] Run tool validation tests — confirm each tool produces correct output on test inputs
- [ ] Write initial commit: `"Phase 0 complete: environment initialized"`

### Completion Gate
- [ ] Hardware detection ran successfully — backend logged to `logs/hardware.log` with GPU model, VRAM, backend, and baseline inference speed
- [ ] PyTorch functional on detected backend
- [ ] Zero hardcoded `"cuda"` strings in any script — confirmed by audit
- [ ] All tooling scripts pass validation tests
- [ ] Full folder structure exists and is committed
- [ ] `mode7_freeform.py` stub exists and is committed
- [ ] `vlm_critic.py` stub exists and is committed
- [ ] `pose_extractor.py` stub exists and is committed
- [ ] `COMPONENT_COMPOSITING_NOTES.md` stub exists and is committed
- [ ] `data/TRAINING_PROVENANCE_MANIFEST.json` initialized as empty array and committed
- [ ] Web UI skeleton is running on localhost — chat panel, preview, and approve/reject are functional
- [ ] All log placeholder files initialized and committed
- [ ] No Phase 0 tasks remain incomplete

---

## Phase 1 — Boot Training
*Build the knowledge base before touching any model or pixel*

### Tasks
- [ ] Research hardware constraints for minimum 6 platforms — write `HARDWARE_CONSTRAINTS.md`
- [ ] Build reference game list — minimum 40 games across 6+ platforms — write `REFERENCE_GAMES.md`
  - Must cite why each game is referenced (specific quality, cited by pixel art community)
  - No single studio or platform exceeds 30% of list
- [ ] Research and evaluate pixel art resources — write `RESOURCE_LIBRARY.md`
  - Minimum 20 resources rated 7+ on evaluation criteria
  - Prioritize resources that explain WHY not just HOW
  - Prioritize annotated critique examples (before/after with expert explanation)
- [ ] Extract universal principles from research — write `PIXEL_ART_THEORY.md`
  - Minimum 20 principles, each supported by evidence from multiple sources
- [ ] Build mistake taxonomy from critique resources — write `MISTAKE_TAXONOMY.md`
  - Minimum 15 failure modes with corrective principles
  - Organized by beginner / intermediate / advanced
- [ ] Build evaluation rubric from research evidence — write `EVALUATION_RUBRIC.md`
  - Every criterion must be specific and measurable
  - Every criterion must be evidenced from research
  - Passing threshold: 95/100

### Completion Gate
- [ ] `HARDWARE_CONSTRAINTS.md` — 6+ platforms documented
- [ ] `REFERENCE_GAMES.md` — 40+ games, 6+ platforms, each with annotated analysis
- [ ] `RESOURCE_LIBRARY.md` — 20+ resources rated 7+
- [ ] `PIXEL_ART_THEORY.md` — 20+ evidenced universal principles
- [ ] `MISTAKE_TAXONOMY.md` — 15+ failure modes with corrective principles
- [ ] `EVALUATION_RUBRIC.md` — complete, measurable, evidenced
- [ ] Git commit: `"Phase 1 complete: Boot Training knowledge base built"`

---

## Phase 2 — Style Bible & Project Foundation
*Lock project-wide constraints before any generation begins*

### Tasks
- [ ] Define and lock `MASTER_PALETTE.md`
  - Organized into named ramp families
  - Every ramp hue-shifted (not just brightness-shifted)
  - All colors verified within SNES 15-bit RGB color space
  - Usage rules documented per ramp family
- [ ] Define and lock `PROPORTION_SYSTEM.md`
  - Canonical dimensions for all sprite contexts (battle, world, overworld, portrait)
  - Head-to-body ratios, limb conventions
  - Overlay grid templates for each context
- [ ] Define and lock `ANIMATION_STANDARD.md`
  - Required animation sets per character type
  - Frame counts locked for each animation type
  - Timing conventions documented
- [ ] Define and lock `LIGHTING_STANDARD.md`
  - Canonical light source direction (default: top-left)
  - Lighting variant rules for environment contexts
- [ ] Initialize `CONTINUITY_MANIFEST.md` (empty, ready for entries)
- [ ] Initialize `CHARACTER_DNA/` directory
- [ ] Initialize `SHEET_LAYOUT/` directory

### Completion Gate
- [ ] All four style bible documents complete and committed
- [ ] All directories initialized
- [ ] Git commit: `"Phase 2 complete: Style Bible locked"`

---

## Phase 3 — Training Data Pipeline
*Curate corpus and prepare model training data*

**⚠️ Time allocation warning (CHANGE-019):** Phase 3 requires approximately 3× the time of the original estimate. The Golden Dataset (Tier 1) is the primary deliverable and requires manual human curation that cannot be automated or rushed. Do not treat it as a cleanup pass after scraping. It is the most important work in this phase.

### Tasks

**Provenance manifest (CHANGE-023) — initialize before collecting any data:**
- [ ] Confirm `data/TRAINING_PROVENANCE_MANIFEST.json` exists (initialized in Phase 0)
- [ ] Confirm `data/pipeline/scraper.py` writes a provenance entry for every sprite before writing it to the corpus — provenance is recorded at ingestion, not retroactively
- [ ] No sprite enters any training tier without a complete manifest entry

**Tier 2 — Broad Corpus:**
- [ ] Build training data scraper and downloader
  - Prioritize: OpenGameArt.org, itch.io free packs, permissively licensed archives
  - Respect explicit scraping blocks on any site
  - Log every source with URL and license status in `data/scraper/sources.md`
  - Only accept CC0, CC-BY, CC-BY-SA licenses — reject CC-BY-NC, CC-BY-ND, unknown
- [ ] Build sprite extraction pipeline
  - Extract individual sprites from sprite sheets
  - Convert to indexed palette format
  - Validate against SNES palette constraints
  - Filter out non-SNES-style sprites
- [ ] Build palette indexing pipeline
  - Convert each sprite to palette-index sequence format
  - Pair each sequence with structured metadata (dimensions, genre, platform, quality estimate)
- [ ] Curate broad corpus — target 30,000–50,000 sprite sequences after filtering
- [ ] Log corpus statistics in `data/corpus_stats.md`: total sprites, by tier, by platform, by genre, by quality tier

**Tier 1 — Golden Dataset (primary quality signal — most important task in Phase 3):**
- [ ] Manually review and curate a Golden Dataset of 3,000–5,000 sprites
  - Every sprite individually verified: correctly extracted, SNES-aesthetic compliant, correctly palette-indexed, free of pillow shading and banding
  - Preferred sources: commissioned sprites, community-contributed CC0 sprites, highest-quality subset of Tier 2 scrape
  - Store in `data/golden/`
  - Record every sprite in `data/golden/CONTRIBUTORS.md` with source and reviewer notes
- [ ] Golden Dataset provenance entries recorded in `data/TRAINING_PROVENANCE_MANIFEST.json` with `"tier": 1`

**Paired-view detection (CHANGE-017):**
- [ ] Build `data/pipeline/view_pair_detector.py` — identifies candidate view pairs within sprite sheets using palette similarity and proportion matching
- [ ] Build `data/pipeline/pair_annotator.py` — presents candidates for human confirmation, writes confirmed pairs with `view_pair_id` and direction labels
- [ ] Run view pair detection across both tiers — confirm minimum 20% of training examples are paired-view sequences
- [ ] Synthetic pairs (simple reflections) may supplement confirmed pairs — label separately with lower training weight

**Structure-aware token ordering (CHANGE-001, CHANGE-014):**
- [ ] Apply four-category pixel classification to all sequences (transparent, outline, structural, non-structural)
  - Note: four categories for Tier 2, `--full-five-category` flag may be used for Tier 1 Golden Dataset where data quality is controlled
- [ ] Reorder token sequences: transparent → outline → structural → non-structural
- [ ] Preserve original (x, y) canvas coordinates alongside each reordered token — output format is `(palette_index, canvas_x, canvas_y)` tuples
- [ ] Log distribution of all four pixel categories across the full corpus
- [ ] Flag any category below 3% representation for review before proceeding

**Anti-pattern dataset:**
- [ ] Programmatically generate 500+ intentionally bad sprites using rule violations
- [ ] Pair with corrected versions and labeled failure modes
- [ ] Used for evaluation engine calibration

- [ ] Split corpus: 90% training, 10% validation

### Completion Gate
- [ ] Tier 1 Golden Dataset contains minimum 3,000 manually curated and verified sprites in `data/golden/`
- [ ] Tier 2 broad corpus contains 30,000+ sprite sequences in palette-index format
- [ ] `data/TRAINING_PROVENANCE_MANIFEST.json` contains an entry for every sprite in both tiers — zero sprites without a manifest entry
- [ ] All sequences stored in structure-aware order with `(palette_index, canvas_x, canvas_y)` tuples
- [ ] Pixel category distribution logged — no category below 3% of total tokens
- [ ] Minimum 20% of training examples are paired-view sequences — documented in `data/corpus_stats.md`
- [ ] Anti-pattern dataset contains 500+ labeled examples
- [ ] Train/validation split documented
- [ ] Data pipeline scripts tested and validated on sample batches
- [ ] Git commit: `"Phase 3 complete: Training corpus ready"`

---

## Phase 4 — Model Architecture & Initial Training
*Build and train the custom transformer*

### Tasks
- [ ] Implement transformer architecture in PyTorch
  - Decoder-only (GPT-style) autoregressive model
  - Input: DNA conditioning tokens + partial sprite sequence
  - Output: next palette index token
  - Sequence length: max sprite width × height (target: 64×64 = 4096)
  - Vocabulary: palette indices (256 max, typically 15 per character)
  - **2D positional encodings required** — each token embedding sums palette index embedding + learned X coordinate embedding + learned Y coordinate embedding. No 1D sequence positional encoding as primary spatial signal. See SPEC.md §3.1 CHANGE-010.
- [ ] Implement DNA conditioning system
  - Structured DNA JSON → conditioning token encoding
  - Conditioning collapses valid token vocabulary to character palette
- [ ] Implement training loop
  - Next-token prediction loss on palette-index sequences
  - Validation loss tracking
  - Checkpoint saving every N steps
  - Early stopping on validation plateau
- [ ] **Write `model/architecture/IMPLEMENTATION_NOTES.md`** documenting every implementation decision in the architecture files: how 2D positional encodings are implemented, how DNA conditioning tokens are handled, how the causal mask interacts with structure-aware token ordering. **HALT and flag for human review before running any training. Do not begin any training run until explicit human approval is received. (CHANGE-020)**
- [ ] Run initial training on full corpus (after human architecture review approval)
  - Log training loss curve
  - Log validation loss curve
  - Save checkpoints at regular intervals
- [ ] Evaluate initial model
  - Generate 100 test sprites from DNA conditioning
  - Score all 100 against rubric automated gate (85pts)
  - Log pass rate and failure mode distribution
- [ ] Run structure-aware ordering experiment
  - Train a parallel model on identical corpus in raster order
  - Compare rubric pass rates on held-out validation set
  - Document result in `logs/training_log.md` — keep whichever performs better
- [ ] Run sequence length risk evaluation (CHANGE-007)
  - Generate 50 sprites across a range of sizes including battle sprites (48×64+)
  - Measure rubric pass rate separately for sequences <1,500 tokens and >1,500 tokens
  - If >1,500 token pass rate < 70%: HALT Phase 4 advancement, implement hierarchical generation
- [ ] Run DNA conditioning consistency measurement (CHANGE-008)
  - Generate 20 battle sprites (48×64 minimum)
  - Run `dna_diff.py` separately on top half vs bottom half of each sprite
  - Log the consistency delta — if bottom half is >10% lower than top half consistently, flag for Phase 6 cross-attention upgrade
- [ ] **Optional MaskGIT speed evaluation (CHANGE-011):** If generating the 100-sprite evaluation batch takes longer than 4 hours wall-clock time on available hardware, document the bottleneck and evaluate MaskGIT as an alternative architecture before proceeding to Phase 5. This gate is only triggered if speed is a demonstrated practical blocker — not a theoretical concern. Speed is not a primary project concern; accuracy is. See README.md On Speed vs. Accuracy.

### Completion Gate
- [ ] `model/architecture/IMPLEMENTATION_NOTES.md` written and human architecture review approval received — no training began before this
- [ ] Model trains without errors to convergence
- [ ] Validation loss below target threshold (defined during training)
- [ ] Initial evaluation: minimum 50/100 sprites passing automated rubric gate (85pts — baseline, proves model is functional)
- [ ] Structure-aware vs raster ordering comparison documented in `logs/training_log.md`
- [ ] Sequence length evaluation completed — pass rates for <1,500 tokens and >1,500 tokens logged separately
- [ ] DNA conditioning consistency measured — top-half vs bottom-half delta logged for 20 battle sprites
- [ ] If sequences >1,500 tokens pass rate < 70%: DO NOT advance to Phase 5. Implement hierarchical generation and re-train. Document decision in `logs/phase_gates.md`.
- [ ] If bottom-half DNA consistency is >10% lower than top-half: document as Phase 6 priority — upgrade to cross-attention conditioning
- [ ] If batch generation exceeded 4 hours wall-clock: MaskGIT evaluation documented before proceeding
- [ ] Git commit: `"Phase 4 complete: Initial model trained"`

---

## Phase 5 — Practice Gauntlet
*Validate model and evaluation engine before production work*

### Tasks
- [ ] Generate 10 complete practice characters
  - Each with full overworld walk cycle (4 directions × 3 frames)
  - Span archetypes: warrior, mage, elderly NPC, child, monster, merchant, villain, etc.
- [ ] Document every failure and rebuild
  - Minimum 3 characters must fail initial generation and require rebuild
  - Every failure logged with specific rubric failure points
  - Every rebuild logged with what was changed and why it worked
- [ ] Validate improvement curve
  - Final 5 characters must show measurably higher average score than first 5
  - Improvement documented in `LESSONS_LEARNED.md`
- [ ] Run group continuity check on all 10 practice characters
  - Generate comparison sheet
  - Evaluate as a group — must look like same world
  - Weakest sprite rebuilt until group passes
- [ ] Validate anti-pattern detection
  - Run evaluation engine against anti-pattern dataset
  - Engine must correctly identify 90%+ of documented failure modes
- [ ] Run 5 freeform Mode 7 test generations
  - Validate DNA/style constraints are correctly bypassed
  - Confirm outputs land in `assets/freeform/` only
  - Confirm continuity manifest is NOT updated by freeform outputs
- [ ] Validate full web UI approval workflow end-to-end
  - Generate a practice sprite → preview in web UI at 1x and 4x → approve via UI → confirm asset committed correctly
  - Test reject + adjustment cycle through UI
  - Confirm freeform tab works independently from project tabs
- [ ] Update `LESSONS_LEARNED.md` with minimum 20 rules from gauntlet experience

### Completion Gate
- [ ] 10 practice characters complete with full walk cycles
- [ ] Minimum 3 rebuild cycles documented with root cause analysis
- [ ] Final 5 show measurable score improvement over first 5
- [ ] Group continuity check passes
- [ ] `LESSONS_LEARNED.md` contains 20+ gauntlet-derived rules
- [ ] Anti-pattern detection rate: 90%+
- [ ] Mode 7 freeform tested — 5 generations confirmed non-DNA, isolated from project state
- [ ] Web UI approval workflow validated end-to-end
- [ ] Git commit: `"Phase 5 complete: Practice Gauntlet passed"`

---

## Phase 6 — Quality Fine-Tuning
*Push model from functional to excellent*

### Tasks
- [ ] Curate fine-tuning dataset from Practice Gauntlet
  - All sprites that scored 95+ go into fine-tuning set
  - Pair with their DNA conditioning inputs
- [ ] Run fine-tuning training pass
  - Lower learning rate than initial training
  - Overfit slightly toward high-quality examples
  - Checkpoint frequently
- [ ] Evaluate fine-tuned model
  - Generate 100 test sprites
  - Score all against rubric
  - Target: 80/100 passing at 95+
- [ ] Iterate fine-tuning until target met
- [ ] Evaluate evaluation engine accuracy
  - Does the engine correctly score sprites that humans would rate similarly?
  - Adjust rubric implementation if systematic errors found
- [ ] Update `LESSONS_LEARNED.md` with fine-tuning learnings

### Completion Gate
- [ ] 80/100 generated sprites passing 95+ rubric
- [ ] Fine-tuning training logs committed
- [ ] Evaluation engine accuracy validated
- [ ] Git commit: `"Phase 6 complete: Quality fine-tuning complete"`

---

## Phase 7 — Production Pipeline Integration
*Wire all components into the complete AM Pixel pipeline*

### Tasks
- [ ] Integrate generation engine with approval pipeline (conversation flow)
- [ ] Integrate DNA extraction into approval confirmation
- [ ] Integrate sheet manager with generation pipeline
- [ ] Integrate continuity checker into production flow
- [ ] Integrate export engine (Godot, RPG Maker MZ, GameMaker, generic JSON)
- [ ] Implement GitHub repo integration (read existing assets, commit on approval)
- [ ] Implement all seven generation modes (character, extension, tileset/parallax, UI, font, battle effects, freeform)
- [ ] Implement project tab organization system
- [ ] Implement seasonal and time-of-day tileset variant generation
- [ ] Implement NPC archetype variant system
- [ ] Implement state-based tile generation (door open/closed, chest open/closed, etc.)
- [ ] Build local inference server (FastAPI endpoint)
- [ ] Implement prompt expansion layer (Mode 5b) — language model API call with SNES style-bible guardrails, editable output, genre-aware system prompt
- [ ] Evaluate animation temporal coherence — generate 5 walk cycles, score Animation Quality rubric category specifically for motion quality (not character quality). If motion quality failures are consistent, implement temporal frame conditioning before Phase 8.
- [ ] End-to-end test: create a complete sample project with 3 characters, 1 tileset, UI, and font

### Completion Gate
- [ ] All seven generation modes functional end-to-end
- [ ] Prompt expansion layer functional and tested with SNES style-bible guardrails active
- [ ] Temporal coherence evaluated — motion quality rubric scores documented, temporal conditioning implemented if needed
- [ ] Complete sample project created and committed to test repo (3 characters, 1 tileset, 1 parallax background, UI, font, 2 battle effects)
- [ ] Export tested in at minimum Godot and RPG Maker MZ
- [ ] GitHub integration tested on real repo
- [ ] Local inference server operational
- [ ] Git commit: `"Phase 7 complete: Full pipeline integrated"`

---

## Phase 8 — Genre 1A Production Threshold
*Achieve 99/100 production quality on Top-Down RPG*

### Tasks
- [ ] Generate production validation batch: 100 sprites across all asset types for Genre 1A
  - Characters (world and battle), enemies, interior tilesets, exterior tilesets, world map tiles, UI, fonts, animated tiles
- [ ] Score all 100 against rubric
- [ ] Count passing sprites (95+)
- [ ] If below 99/100: identify failure patterns, run targeted fine-tuning, repeat
- [ ] Document every failure pattern in `MISTAKE_TAXONOMY.md`
- [ ] Update `LESSONS_LEARNED.md` with production learnings
- [ ] Human evaluation: present a set of AM Pixel sprites alongside SNES reference sprites — can the evaluator reliably distinguish them?

### Completion Gate
- [ ] 99/100 production validation sprites pass 95+ rubric
- [ ] Human evaluation: evaluator cannot reliably distinguish AM Pixel from SNES reference
- [ ] `LESSONS_LEARNED.md` contains 50+ rules from real production experience
- [ ] Git commit: `"Phase 8 complete: Genre 1A production threshold met"`
- [ ] **UNLOCK: Begin Genre 1B (Action Adventure) training**

---

## Phase 9+ — Progressive Genre Expansion

After Phase 8, each subsequent genre follows the same pattern:
1. Research phase specific to new genre
2. Targeted fine-tuning on genre-specific corpus
3. Practice gauntlet for new genre
4. Production validation batch (99/100 threshold)
5. Human evaluation
6. Unlock next genre

Genre progression order follows `GENRE_TAXONOMY.md` tier structure.

---

## Phase 10 — Server Infrastructure (When Ready for Market)

- [ ] Deploy model to inference server
- [ ] Build server-side inference API
- [ ] Implement user authentication and generation quotas
- [ ] Implement freemium tier logic
- [ ] Build client application (web or desktop)
- [ ] End-to-end testing of full server-client pipeline

This phase does not begin until Genre 1A production threshold is met and the tool is validated as genuinely excellent.

---

## Escalation Protocol

If OpenClaw is blocked on any task for more than 48 hours:
1. Document the specific blocker in `BLOCKERS.md`
2. Document what was attempted and why it failed
3. Halt only the blocked task — continue other parallel work if possible
4. Flag for human review with a clear description of options

Do not silently fail. Do not work around a fundamental problem without documenting it. Do not advance a phase gate if a blocker is unresolved.

---

*AM Pixel Execution Roadmap v1.4 | Absentmind Studio*

---

## Changelog

### v1.3 — 2026-04-12
- **CHANGE-019:** Phase 3 completely rewritten with two-tier corpus strategy. 3× time allocation warning added — manual curation cannot be automated or rushed. Tier 1 Golden Dataset (3,000–5,000 sprites, manually verified) established as primary Phase 3 deliverable. Tier 2 broad corpus (30,000–50,000) for volume training. Provenance manifest required before any data collection begins.
- **CHANGE-017:** Phase 3 Tasks — added view_pair_detector.py and pair_annotator.py tasks; minimum 20% paired-view sequence target; synthetic pairs (reflections) permitted at lower training weight; teaches model view rotation geometry implicitly.
- **CHANGE-023:** Phase 0 Tasks — TRAINING_PROVENANCE_MANIFEST.json initialized as empty array; Phase 3 gate — manifest entry required for every sprite before ingestion, zero sprites without entry.
- **CHANGE-014:** Phase 3 — pixel classifier updated to four categories in task description; (palette_index, canvas_x, canvas_y) output tuple format noted.
- **CHANGE-010:** Phase 4 Tasks — 2D positional encoding requirement added explicitly to transformer implementation task; note that 1D encodings are architecturally incompatible with structure-aware ordering.
- **CHANGE-020:** Phase 4 Tasks — mandatory architecture review gate added. OpenClaw must write IMPLEMENTATION_NOTES.md documenting every decision in model/architecture/ files (2D positional encodings, DNA conditioning, causal mask), halt, and await explicit human approval before any training run begins.
- **CHANGE-011:** Phase 4 Tasks — optional MaskGIT speed evaluation gate added; triggered only if batch generation exceeds 4 hours wall-clock time; speed is not a primary concern, only triggered as practical blocker.
- **CHANGE-015/021/022:** Phase 0 Tasks — stub initialization tasks added for pose_extractor.py, vlm_critic.py, COMPONENT_COMPOSITING_NOTES.md; all added to Phase 0 completion gate.
- Phase 4 completion gate updated to reflect 85-point automated rubric gate (not 95) for unattended batch evaluation.
- **CHANGE-018:** Changelog section added.

### v1.4 — 2026-04-19
- Bible **v1.4**: per Document Hygiene Rules, all Bible documents incremented together; canonical tree after `bible-v1.3-apr13` is **`bible-v1.4`** (no additional roadmap task delta in this entry).

### v1.2 — 2026-04-11
- **CHANGE-003:** Phase 0 Tasks — replaced CUDA-only GPU verification with universal hardware detection via detector.py; log backend to hardware.log; proceed on any tier. Added task to audit all scripts for hardcoded "cuda" strings (zero permitted). Added log placeholder file initialization task.
- Phase 0 Completion Gate — replaced "GPU confirmed with CUDA" with hardware detection logged gate; added zero hardcoded "cuda" strings gate; added log placeholder files initialized gate.
- **CHANGE-001:** Phase 3 Tasks — added structure-aware token ordering: pixel_classifier.py classification step, sequence_reorderer.py reordering step, (x,y) positional encoding preservation, category distribution logging, 3% floor flag.
- Phase 3 Completion Gate — added structure-aware ordering gate; added pixel category distribution gate (no category below 3%).
- **CHANGE-007:** Phase 4 Tasks — added sequence length risk evaluation: generate 50 sprites across size range, measure pass rates separately for <1,500 and >1,500 tokens, HALT gate if >1,500 token rate < 70%.
- **CHANGE-001:** Phase 4 Tasks — added structure-aware vs raster ordering comparison experiment; document result in training_log.md, keep whichever performs better.
- **CHANGE-008:** Phase 4 Tasks — added DNA conditioning consistency measurement: 20 battle sprites, top-half vs bottom-half dna_diff.py comparison, flag for Phase 6 cross-attention upgrade if delta > 10%.
- Phase 4 Completion Gate — added all three experiment gate criteria with explicit HALT conditions.
- Phase 7 Tasks — updated "five generation modes" to "seven generation modes."
- **CHANGE-002:** Phase 7 Tasks — added prompt expansion layer (Mode 5b) implementation task with SNES guardrails requirement.
- **CHANGE-009:** Phase 7 Tasks — added temporal coherence evaluation task: generate 5 walk cycles, score Animation Quality for motion quality specifically, implement temporal frame conditioning if motion failures are consistent.
- Phase 7 Completion Gate — added prompt expansion functional gate; added temporal coherence evaluated gate; updated sample project to include parallax background and battle effects.

### v1.1 — 2026-04-11
- Phase 0 Tasks: Added mode7_freeform.py stub creation as required task.
- Phase 0 Tasks: Added ui/ directory initialization with web UI skeleton (chat panel, 1×/4× preview, approve/reject/adjust, project tabs, freeform tab) — must be functional before Phase 5.
- Phase 0 Completion Gate: Added mode7_freeform.py stub gate criterion.
- Phase 0 Completion Gate: Added web UI skeleton functional gate criterion.
- Phase 5 Tasks: Added 5 freeform Mode 7 test generations — validate DNA/style constraints bypassed, outputs isolated to assets/freeform/, continuity manifest not updated.
- Phase 5 Tasks: Added full web UI approval workflow end-to-end validation — generate, preview, approve, confirm commit; test reject + adjustment cycle; confirm freeform tab independent.
- Phase 5 Completion Gate: Added Mode 7 freeform isolation gate.
- Phase 5 Completion Gate: Added web UI workflow validation gate.
- Added ⚠️ CRITICAL DEFINITION section at top of document — mirrors SPEC.md threshold fix (95/100 = individual score, 99/100 = batch pass rate with concrete examples).

### v1.0 — Original Release
- Phases 0–10 defined: initialization through server infrastructure.
- Phase 0: CUDA-only hardware verification with halt condition if CUDA not found.
- Phase 1: Boot Training knowledge base with 6 completion gate criteria.
- Phase 2: Style Bible lockdown.
- Phase 3: Training data pipeline (50,000+ corpus target).
- Phase 4: Model architecture and initial training.
- Phase 5: Practice Gauntlet (10 characters, minimum 3 rebuild cycles).
- Phase 6: Quality fine-tuning (80/100 target).
- Phase 7: Production pipeline integration (5 modes at this version).
- Phase 8: Genre 1A production threshold (99/100 batch gate).
- Phase 9+: Progressive genre expansion following GENRE_TAXONOMY.md tier structure.
- Phase 10: Server infrastructure (deferred until Genre 1A met).
- Escalation protocol: 48-hour blocker documentation and human flag requirement.
