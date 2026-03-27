# AM Pixel — Execution Roadmap
**Absentmind Studio | Version 1.1**

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
- [ ] Verify NVIDIA GPU available with CUDA support — log GPU model, VRAM, CUDA version
- [ ] Verify PyTorch CUDA installation functional
- [ ] Initialize full folder structure per `FOLDER_STRUCTURE.md`
- [ ] Initialize git repo (or connect to existing GitHub repo)
- [ ] Install all required Python dependencies — log versions
- [ ] Verify disk space — minimum 100GB available for training data and model checkpoints
- [ ] Build all required tooling scripts (palette_validator, dna_diff, rubric_scorer, sheet_manager, etc.)
- [ ] Create `pipeline/modes/mode7_freeform.py` stub with documented interface
- [ ] Initialize `ui/` directory — build working web UI skeleton: chat panel, 1×/4× image preview, approve/reject/adjust controls, project tabs, freeform tab. Must be functional before Phase 5.
- [ ] Run tool validation tests — confirm each tool produces correct output on test inputs
- [ ] Write initial commit: `"Phase 0 complete: environment initialized"`

### Completion Gate
- [ ] GPU confirmed with CUDA, VRAM logged
- [ ] All tooling scripts pass validation tests
- [ ] Full folder structure exists and is committed
- [ ] `mode7_freeform.py` stub exists and is committed
- [ ] Web UI skeleton is running on localhost — chat panel, preview, and approve/reject are functional (content not required yet, structure must work)
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

### Tasks
- [ ] Build training data scraper and downloader
  - Prioritize: OpenGameArt.org, itch.io free packs, permissively licensed archives
  - Respect explicit scraping blocks on any site
  - Log every source with URL and license status
- [ ] Build sprite extraction pipeline
  - Extract individual sprites from sprite sheets
  - Convert to indexed palette format
  - Validate against SNES palette constraints
  - Filter out non-SNES-style sprites
- [ ] Build palette indexing pipeline
  - Convert each sprite to palette-index sequence format
  - Pair each sequence with structured metadata (dimensions, genre, platform, quality estimate)
- [ ] Curate training corpus
  - Run initial quality filter — remove low-quality sprites
  - Minimum corpus target: 50,000 sprite sequences
  - Log corpus statistics: total sprites, by platform, by genre, by quality tier
- [ ] Build anti-pattern dataset
  - Programmatically generate 500+ intentionally bad sprites using rule violations
  - Pair with corrected versions and labeled failure modes
  - Used for evaluation engine calibration
- [ ] Split corpus: 90% training, 10% validation

### Completion Gate
- [ ] Corpus contains 50,000+ sprite sequences in palette-index format
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
- [ ] Implement DNA conditioning system
  - Structured DNA JSON → conditioning token encoding
  - Conditioning collapses valid token vocabulary to character palette
- [ ] Implement training loop
  - Next-token prediction loss on palette-index sequences
  - Validation loss tracking
  - Checkpoint saving every N steps
  - Early stopping on validation plateau
- [ ] Run initial training on full corpus
  - Log training loss curve
  - Log validation loss curve
  - Save checkpoints at regular intervals
- [ ] Evaluate initial model
  - Generate 100 test sprites from DNA conditioning
  - Score all 100 against rubric
  - Log pass rate and failure mode distribution

### Completion Gate
- [ ] Model trains without errors to convergence
- [ ] Validation loss below target threshold (defined during training)
- [ ] Initial evaluation: minimum 50/100 sprites passing rubric (baseline — model is not good yet, this just proves it's functional)
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
- [ ] Implement all five generation modes (character, extension, tileset, UI, font)
- [ ] Implement project tab organization system
- [ ] Implement seasonal and time-of-day tileset variant generation
- [ ] Implement NPC archetype variant system
- [ ] Implement state-based tile generation (door open/closed, chest open/closed, etc.)
- [ ] Build local inference server (FastAPI endpoint)
- [ ] End-to-end test: create a complete sample project with 3 characters, 1 tileset, UI, and font

### Completion Gate
- [ ] All five generation modes functional end-to-end
- [ ] Complete sample project created and committed to test repo
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

*AM Pixel Execution Roadmap v1.0 | Absentmind Studio*
