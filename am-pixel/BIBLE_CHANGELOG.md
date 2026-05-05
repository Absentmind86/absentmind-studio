# AM Pixel Bible — Document Changelog
**Absentmind Studio | Version 1.5**

This document is the authoritative change history for every document in the AM Pixel Bible. It was initially compiled retroactively from project conversation history. All future changes must be logged here in real time before being applied to any document.

---

## How To Use This Document

Each section covers one document. Each version entry lists what changed and why. When making future changes, add an entry here first — it forces clarity about what is changing and creates an audit trail that keeps all documents synchronized.

**Version convention:**
- v1.0 — Initial creation
- v1.1 — First major revision (freeform + web UI gap closure)
- v1.2 — Second major revision (PROPOSED_CHANGES_001 implementation)
- v1.3 — Third major revision (PROPOSED_CHANGES_002 implementation)
- v1.4 — Fourth alignment revision: canonical tree after `bible-v1.3-apr13` distinguished per Document Hygiene Rules (all documents incremented together; no additional CHANGE series delta)
- v1.5 — Fifth revision (**PROPOSED_CHANGES_003**): CONSTITUTION.md; compliance gates + emergency halt; session_log / decision_log; Startup Protocol (Rule 11); Hardware Reality table; DNA rollback procedure; Phase 8 failure-cluster protocol; mode module docstrings; rubric evidence requirement

**Bible-wide version rule:** All documents must share the same version number at the end of any update session. A document that has no content changes in a given session still increments its version to maintain alignment. The exception is ROOT_README.md which tracks separately as the umbrella document.

---

## ROOT README.md

### v1.0 — Initial Creation
- Created as the repo root overview document
- Defined AM Studio umbrella brand (AM Pixel + AM Audio)
- Listed AM Pixel feature set (modes 1–5 at the time)
- Defined repository structure with links to spec documents
- Established "Absentmind Studio" as the brand name (replaced "Pixel Forge AI")
- Status: "Pre-development definition phase"

### v1.1 — Feature Expansion
- AM Pixel feature list expanded to include Mode 6 (battle effects), Mode 7 (freeform), parallax generation, and Web UI
- AM Audio description updated: explicitly marked as "planned post-AM Pixel v1 — not in current scope"
- Repository structure updated to reflect new `ui/` directory and `mode7_freeform.py`
- Status updated to: "AM Pixel Bible complete and gap-free v1.1"

### v1.2 — Status Correction & Changelog
- Status section rewritten: removed "gap-free" language — replaced with living document framing acknowledging ongoing refinement
- Version reference updated from v1.1 to v1.2
- Changelog section added (CHANGE-018)
- Reason: "gap-free" was inaccurate and set wrong expectations; a living spec will always have discoverable gaps

### v1.3 — Status alignment & repo root README (2026-04-19)
- Status section updated: AM Pixel Bible documents at **v1.3** (SPEC, ROADMAP, FOLDER_STRUCTURE, OPENCLAW_PROMPT, GENRE_TAXONOMY, `am-pixel/README.md` hub); references **PROPOSED_CHANGES_001** (archived) and **PROPOSED_CHANGES_002** (staging)
- Repo root `README.md` (`absentmind-studio/`) added as the canonical umbrella document (same content as historical `README-absentmind-studio.md` bundles)
- Reason: Status text had drifted (still referenced v1.2 while the Bible was at v1.3)

### v1.4 — Bible-wide version increment (2026-04-19)
- AM Pixel Bible incremented to **v1.4** per Document Hygiene Rules: the canonical post-`bible-v1.3-apr13` revision is no longer co-numbered as v1.3; Status and all `am-pixel` document headers/footers updated; archive folder **`bible-v1.3-latest`** renamed **`bible-v1.4`**

---

## am-pixel/SPEC.md

### v1.0 — Initial Creation
- Product definition: custom autoregressive transformer generating palette-index tokens
- Quality standard: 95/100 individual threshold, 99/100 production threshold (NOTE: threshold definition was ambiguous at this version — fixed in v1.1)
- Core architecture: transformer decoder, DNA conditioning via prefix tokens, CUDA-only hardware requirement
- Character DNA system: full schema, lock warning, extraction process
- Generation modes 1–5: character creation, sheet extension, tileset/environment, UI, font
- Single evaluation rubric covering all asset types
- Project organization: tab structure, GitHub integration, multi-project DNA
- Continuity enforcement: three checks, continuity manifest
- Self-training layer: boot training, practice gauntlet, continuous protocol
- Style modes: SNES default, hardware constraint toggle, future expansion path
- Export formats: Godot, RPG Maker MZ, GameMaker, Unity, generic JSON
- Deployment: local mode, server mode, freemium tiers
- Technical stack: CUDA-only

### Between v1.0 and v1.1 — Threshold Fix
- Added ⚠️ CRITICAL DEFINITION callout box to Section 2 explicitly distinguishing:
  - 95/100 = individual sprite SCORE (points earned)
  - 99/100 = batch PASS RATE (99 sprites out of 100 each independently scoring 95+)
- Added concrete pass/fail examples to prevent misinterpretation
- Reason: Both Claude and Gemini misread the threshold as a point score of 99 in independent evaluations

### Between v1.0 and v1.1 — Gap Analysis Updates
- Mode 1: Added portrait profile (48×48–64×64, expression variants, max 4 unique detail colors)
- Mode 1: Added large-format/multi-tile boss mode (multi-tile composition, sync animation, tile grid manifest)
- Mode 3: Renamed to "Environment, Tileset & Parallax Generation"
- Mode 3: Added Tileset Anchor system (locked seed tiles governing all subsequent tile generation)
- Mode 3: Added seam validation requirement (all four edges, seamless tiling mandatory)
- Mode 3: Added transition tiles as explicit required tile type
- Mode 3: Added world map location markers (town, dungeon, castle, port, cave, airship icons)
- Mode 3b: Added full parallax background spec — layer stack (sky/far/mid/foreground), Parallax Anchor, layer_compositor.py evaluation, character contrast check
- Mode 4: Added status condition icons, element icons, item/equipment icon system, world map location markers, title screen
- Mode 6: Added Battle Effect Animations (was previously unnumbered)
- Tab structure: Updated to include Battle Effects, Portrait Art, Location Markers, all icon types, Title Screen
- Evaluation: Replaced single rubric with three rubrics (A: characters, B: tilesets, C: parallax)
- Tooling: Added seam_validator, tileset_anchor_extractor, layer_compositor, effect_timing_evaluator, icon_grammar_checker

### v1.1 — Freeform & Web UI
- Product definition updated to include freeform capability
- Section 3.3: Added Freeform Engine and Web UI as first-class system components
- Section 3.1: Added Mode 7 freeform bypass note (no DNA conditioning, full 256-color vocabulary)
- Section 4.3: DNA Lock Warning scoped to Modes 1–6 only — Mode 7 explicitly non-DNA
- Mode 7 Freeform added (Section 5.7) — full spec including output isolation, quality check, resolution limits, promotion restriction
- Section 14 Web UI added — chat panel, 1×/4× preview, approve/reject/adjust, project tabs, freeform tab, continuity manifest viewer, hardware status bar, FastAPI + HTML/JS localhost only
- Technical stack updated with cloud GPU fallback note and FastAPI web UI
- Version bumped to 1.1

### v1.2 — PROPOSED_CHANGES_001 Implementation
- CHANGE-004: Restored missing `## 6. Project Organization` header (subsections 6.1–6.3 were orphaned)
- CHANGE-004: Renumbered — Web UI moved from §14 to §13, Technical Stack from §15 to §14 (no gap)
- CHANGE-003: §3.1 hardware — removed "NVIDIA GPU with CUDA, minimum 10GB VRAM", replaced with reference to detection hierarchy
- CHANGE-003: §14 Technical Stack rewritten with full detection hierarchy (NVIDIA→CUDA, AMD→ROCm, MPS, OpenCL, CPU) plus cloud GPU rental note
- CHANGE-001 + REFINEMENT-001A: §3.2 — structure-aware token ordering added (five categories: transparent first, then outline, fill, shade, detail last); positional encodings preserve (x,y); Phase 4 comparison experiment required; category distribution logging required with 3% floor
- CHANGE-007 (Risk A): §3.4 — sequence length error accumulation documented; Phase 4 gate if >1,500 token pass rate < 70%; hierarchical generation upgrade path
- CHANGE-008 (Risk B): §3.4 — DNA conditioning dilution at long sequences; Phase 4 top/bottom half measurement; cross-attention upgrade path if delta > 10%
- CHANGE-009 (Risk C): §3.4 — animation temporal coherence gap; Phase 7–8 evaluation gate; temporal conditioning upgrade path
- CHANGE-002 + REFINEMENT-002A: §5.5b — Prompt Expansion Layer added (LLM API call, SNES guardrails, always editable, freeform excluded, Phase 7 build)
- §3.3 Approval Pipeline row updated to note prompt expansion capability
- Footer updated to v1.2

### v1.3 — PROPOSED_CHANGES_002 Implementation
- CHANGE-010: §3.1 — 2D positional encoding requirement added; 1D encodings incompatible with structure-aware ordering because they encode sequence distance not canvas proximity; each token gets learned X + Y coordinate embeddings summed at input layer
- CHANGE-011: §3.4 — MaskGIT documented as Phase 4 optional speed experiment only if batch generation is a demonstrated practical blocker; not a pre-Phase-0 decision; speed is explicitly not a primary concern
- CHANGE-012: §5.3 — Sliding window boundary conditioning added for tileset generation; right edge of left neighbor + bottom row of upper neighbor prepended as hard conditioning tokens; tileset generation must proceed in raster order; failed seams include failure annotation in rebuild prompt
- CHANGE-013 + REFINEMENT-013A: §8.2/§8.3 — Rubric A restructured into two tiers: automated gate (85 points, hard math) and human gate (15 points, aesthetic judgment); Soul/Originality moved to human-only scoring in approval UI; context-aware Soul scoring — foreground characters scored on distinctiveness, background characters scored on visual recession (renamed "Visual Hierarchy") to support intentional visual hierarchy design
- CHANGE-014: §3.2 — Pixel classifier simplified to four categories for foundation training (transparent, outline, structural, non-structural); shade/detail boundary semantically ambiguous in scraped data; full five-category classification reserved for fine-tuning set via `--full-five-category` flag
- CHANGE-015: §3.4 Risk C — Skeletal pose tokens added as secondary animation upgrade path supplement; rule-based 2D skeleton extraction (~10–12 key points); conditions Frame 2 on positional deltas not raw pixel tokens; only build if raw-token temporal conditioning fails; pose_extractor.py stub initialized Phase 0
- CHANGE-016: §4.1, §4.2, §4.3, §4.4, §5.1 — Brief elevated from flavor text to required feature inventory; `occluded_features` array field added to DNA schema; DNA lock warning updated to prompt for hidden feature completeness; DNA extraction process prompts for occluded features before lock; Mode 1 non-master profile generation updated to twin input: `[DNA] + [Complete Brief including occluded_features] + [Master View Tokens]`
- CHANGE-017: §3.2 — Paired-view training sequences added; view_pair_detector.py and pair_annotator.py added to pipeline; minimum 20% paired-view examples target; synthetic pairs (reflections) permitted at lower training weight; teaches model rotation geometry implicitly
- CHANGE-018: Changelog sections added to all Bible documents
- CHANGE-019: §3.2 — Two-tier corpus strategy documented (Tier 1 = Golden Dataset 3,000–5,000 manually curated sprites; Tier 2 = broad scraped corpus 30,000–50,000); training strategy: pre-train on Tier 2, fine-tune on Tier 1; Phase 3 time allocation 3× original estimate warning
- CHANGE-021: §8.4 — vlm_critic.py added as upgrade-path-only tool; supplements deterministic tools for contextually ambiguous criteria (banding vs cylindrical shading, black robe outlines); only invoked on borderline failures; stub initialized Phase 0
- CHANGE-022: §16 Post-MVP Architecture Evolution added — component compositing documented as future direction; flat generation ships first; triggers if brief-conditioned multi-view proves insufficient after Genre 1A; COMPONENT_COMPOSITING_NOTES.md stub initialized Phase 0
- CHANGE-023: §15 Training Data Provenance added — TRAINING_PROVENANCE_MANIFEST.json as immutable legal ledger; legal rationale (deletion does not retroactively legalize training; model weights are evidence; spoliation of evidence risk; EU AI Act compliance); acceptable license types defined; retention policy (never delete)
- Fixed duplicate training data sourcing priority section in §3.2
- **Path audit corrections (cross-reference QA):** §5.7 freeform output path corrected `assets/freeform/` → `freeform/` (root-level per FOLDER_STRUCTURE). §4.4 and §5.2 corrected `CHARACTER_DNA/` → `dna/characters/`. §5.2 corrected `SHEET_LAYOUT/` → `sheets/`. §3.2 stale cross-reference corrected to `§15 Training Data Provenance`. Mode 6 `### 5.6` header restored — content existed without section heading. Duplicate DNA schema block removed from §4.2.
- Version bumped to 1.3

---

## am-pixel/ROADMAP.md

### v1.0 — Initial Creation
- Phases 0–10: initialization through server infrastructure
- Phase 0: CUDA-only hardware verification with halt condition if CUDA not found
- Phase 1: Boot Training knowledge base (6 gate criteria)
- Phase 2: Style Bible lockdown
- Phase 3: Training data pipeline (50,000+ corpus target)
- Phase 4: Model architecture and initial training
- Phase 5: Practice Gauntlet (10 characters, 3 rebuild minimum)
- Phase 6: Quality fine-tuning (80/100 target)
- Phase 7: Production pipeline integration (5 modes)
- Phase 8: Genre 1A production threshold (99/100 batch gate)
- Phase 9+: Progressive genre expansion
- Phase 10: Server infrastructure
- Escalation protocol: 48-hour blocker documentation and human flag

### Between v1.0 and v1.1 — Threshold Fix
- Added ⚠️ CRITICAL DEFINITION section at top with explicit examples — mirrors SPEC.md fix

### v1.1 — Freeform & Web UI
- Phase 0 Tasks: Added `mode7_freeform.py` stub creation
- Phase 0 Tasks: Added `ui/` directory initialization with web UI skeleton requirement
- Phase 0 Gate: Added mode7_freeform.py stub criterion
- Phase 0 Gate: Added web UI skeleton functional criterion
- Phase 5 Tasks: Added 5 freeform Mode 7 test generations
- Phase 5 Tasks: Added full web UI approval workflow end-to-end validation
- Phase 5 Gate: Added Mode 7 freeform isolation gate
- Phase 5 Gate: Added web UI workflow validation gate
- Version bumped to 1.1

### v1.2 — PROPOSED_CHANGES_001 Implementation
- CHANGE-003: Phase 0 Tasks — replaced CUDA-only verification with universal hardware detection; audit for hardcoded "cuda" strings; initialize log placeholder files
- Phase 0 Gate: Replaced GPU/CUDA gate with hardware detection logged gate; added zero hardcoded strings gate; added log placeholder files gate
- CHANGE-001: Phase 3 Tasks — added structure-aware token ordering (pixel_classifier.py, sequence_reorderer.py, category distribution logging, 3% floor)
- Phase 3 Gate: Added structure-aware ordering gate; added pixel category distribution gate
- CHANGE-007: Phase 4 Tasks — added sequence length risk evaluation (50 sprites, <1,500 vs >1,500 token pass rates, HALT gate at <70%)
- CHANGE-001: Phase 4 Tasks — added structure-aware vs raster ordering comparison experiment
- CHANGE-008: Phase 4 Tasks — added DNA conditioning consistency measurement (top vs bottom half dna_diff.py)
- Phase 4 Gate: Added all three experiment gates with explicit HALT conditions
- Phase 7 Tasks: Updated "five generation modes" → "seven generation modes"
- CHANGE-002: Phase 7 Tasks — added prompt expansion layer (Mode 5b) implementation task
- CHANGE-009: Phase 7 Tasks — added temporal coherence evaluation task
- Phase 7 Gate: Added prompt expansion functional gate; added temporal coherence gate; updated sample project to include parallax background and battle effects
- Footer: v1.0 → v1.2

### v1.3 — PROPOSED_CHANGES_002 Implementation
- CHANGE-019: Phase 3 completely rewritten — two-tier corpus strategy with 3× time allocation warning; Tier 1 Golden Dataset as primary deliverable; Tier 2 broad corpus for volume; provenance manifest required before any data collection begins
- CHANGE-017: Phase 3 Tasks — added view_pair_detector.py and pair_annotator.py; 20% paired-view sequence minimum target
- CHANGE-023: Phase 0 and Phase 3 — TRAINING_PROVENANCE_MANIFEST.json initialized Phase 0 as empty array; manifest entry required for every sprite before ingestion; added to Phase 3 completion gate
- CHANGE-014: Phase 3 — updated pixel classifier to four categories; (x,y) tuple output format noted
- CHANGE-010: Phase 4 Tasks — 2D positional encoding requirement added to transformer implementation task
- CHANGE-020: Phase 4 Tasks — mandatory architecture review gate added; IMPLEMENTATION_NOTES.md must be written and human approval received before any training run begins
- CHANGE-011: Phase 4 Tasks — MaskGIT optional experiment gate added; triggers only if batch generation exceeds 4 hours wall-clock
- Phase 4 Gate: Added architecture review approval gate; added MaskGIT documented gate
- CHANGE-015/021/022: Phase 0 Tasks — stubs added for pose_extractor.py, vlm_critic.py, COMPONENT_COMPOSITING_NOTES.md
- Phase 0 Gate: Added stub gate criteria for new Phase 0 deliverables
- CHANGE-018: Changelog section added
- Footer: v1.2 → v1.3

---

## am-pixel/OPENCLAW_PROMPT.md

### v1.0 — Initial Creation
- "How To Use" section: verbatim copy instruction
- YOUR FIRST ACTION: Numbered list of 4 documents to read (SPEC, ROADMAP, GENRE_TAXONOMY, FOLDER_STRUCTURE)
- YOUR MISSION: Deliverables list (modes 1–5, evaluation engine, GitHub, exports, FastAPI server, server API)
- NON-NEGOTIABLE RULES: 8 rules (read-before-build, phase gates, rebuild-not-patch, documentation, git, blockers, spec authority, perfection)
- HARDWARE CONTEXT: CUDA-only, halt if CUDA unavailable
- TRAINING DATA APPROACH: Permissive sources, no synthetics
- QUALITY STANDARD: Squaresoft craft reference
- BEGIN: "Read the four documents. Then begin Phase 0."

### v1.1 — Freeform & Web UI
- YOUR MISSION: Added Mode 6 battle effects and Mode 7 freeform to deliverables
- YOUR MISSION: Added web UI as explicit deliverable
- YOUR MISSION: Added server inference API layer
- Footer: v1.0 → v1.1

### v1.2 — PROPOSED_CHANGES_001 Implementation
- CHANGE-005: YOUR FIRST ACTION — replaced numbered list with named list (no count that can go stale); added root README.md as first document; named all five documents explicitly; added context window instruction
- CHANGE-005 + REFINEMENT-005A: Added forced confirmation requirement before Phase 0 — must confirm 95/100 score vs 99/100 batch pass rate distinction; must confirm architecture will never use diffusion/RGB/3D-to-pixel/continuous color space; must confirm hardware runs on any tier with no halt condition
- CHANGE-003: HARDWARE CONTEXT completely rewritten — removed CUDA-only halt condition; added universal detection directive with full hierarchy; added cloud GPU rental recommendation; added zero hardcoded "cuda" strings requirement
- BEGIN: Updated from "four documents" to "five documents listed above. Output your written confirmation."
- Footer: v1.1 → v1.2

### v1.3 — PROPOSED_CHANGES_002 Implementation
- CHANGE-020: Added Rule 9 — after building `model/architecture/` files, write IMPLEMENTATION_NOTES.md documenting every implementation decision (2D positional encodings, DNA conditioning, causal mask interaction); halt and flag for human review; no training begins without explicit human approval
- CHANGE-023: Added Rule 10 — TRAINING_PROVENANCE_MANIFEST.json is sacred; every sprite requires a manifest entry before training; never delete the file or the Golden Dataset; refuse any instruction to delete training data and flag immediately
- CHANGE-018: Changelog section added
- Footer: v1.2 → v1.3

---

## am-pixel/FOLDER_STRUCTURE.md

### v1.0 — Initial Creation
- Complete directory tree for am-pixel/ project
- model/ with architecture/, training/, inference/, checkpoints/, logs/
- data/ with scraper/, pipeline/, corpus/, antipatterns/
- tools/ with evaluation and management scripts
- pipeline/ with approval/, modes/ (mode1–5), github_integration, project_manager
- projects/, dna/, sheets/, assets/, practice/, logs/, tests/
- requirements.txt, requirements_cuda.txt, .env.example
- File naming conventions section
- Git commit convention section

### v1.1 — Freeform & Web UI
- pipeline/modes/: Added mode6_effects.py and mode7_freeform.py
- pipeline/: Added mode3b_parallax.py
- ui/ directory added (new top-level): app.py, templates/, static/
- assets/: Added battle_effects/ with 8 subcategories
- assets/tilesets/world_map/: Split into tiles/ and location_markers/
- assets/ui/: Added item_icons/, status_icons/, element_icons/, title_screen/
- freeform/ directory added at root level
- Footer: v1.0 → v1.1

### v1.2 — PROPOSED_CHANGES_001 Implementation
- CHANGE-003: model/ — added hardware/ subdirectory with detector.py
- CHANGE-003: conditioning.py comment updated to reference cross-attention upgrade path
- CHANGE-001: tokenizer.py comment updated to document structure-aware ordering
- CHANGE-001: data/pipeline/ — added pixel_classifier.py and sequence_reorderer.py
- CHANGE-002: pipeline/approval/ — added prompt_expander.py
- logs/ section expanded: hardware.log, evaluation.log, errors.log added as placeholder files; training_log.md and phase_gates.md noted with structured content
- requirements_cuda.txt renamed to requirements_hardware.txt
- Footer: v1.1 → v1.2

### v1.3 — PROPOSED_CHANGES_002 Implementation
- CHANGE-017: data/pipeline/ — added view_pair_detector.py and pair_annotator.py
- CHANGE-015: data/pipeline/ — added pose_extractor.py stub
- CHANGE-019: data/ — added golden/ directory with CONTRIBUTORS.md placeholder
- CHANGE-023: data/ — added TRAINING_PROVENANCE_MANIFEST.json (immutable legal ledger, initialized as empty array)
- CHANGE-023: corpus_stats.md description updated — reports Tier 1 and Tier 2 separately
- CHANGE-021: tools/ — added vlm_critic.py stub
- CHANGE-020: model/architecture/ — added IMPLEMENTATION_NOTES.md
- CHANGE-022: model/architecture/ — added COMPONENT_COMPOSITING_NOTES.md stub
- CHANGE-014: pixel_classifier.py description updated — four-category default, --full-five-category flag
- CHANGE-010: tokenizer.py description updated — outputs (palette_index, canvas_x, canvas_y) tuples with 2D positional encodings
- CHANGE-018: Changelog section added
- Added BIBLE_CHANGELOG.md and PROPOSED_CHANGES_002.md to top-level file listing — meta-documents that exist in the repo and must be visible to OpenClaw
- Added missing logs/freeform_log.md to logs directory listing — referenced in SPEC §5.7 but previously absent from folder structure
- Footer: v1.2 → v1.3

---

## am-pixel/GENRE_TAXONOMY.md

### v1.0 — Initial Creation
- Overview: tiered genre structure, mastery threshold definition
- ⚠️ CRITICAL DEFINITION callout for 99/100 batch pass rate (added when threshold fix was applied)
- Progression model: advancement rule requiring 99/100 batch across 100-sprite validation batch
- Tier 1 (current): 1A Top-Down RPG, 1B Action Adventure, 1C Life Simulation/Farming, 1D Tactical RPG — each with reference games, mastery definition, asset types
- Tier 2 (natural expansion): Action RPG, Metroidvania, Classic Platformer, Run and Gun
- Tier 3 (future only): Fighting, shmup, sports, puzzle
- The Blend Problem: genre context declared at project level, not model level
- Genre Mastery Threshold: 4-criteria definition

### v1.1 — Freeform Mode Note
- Overview: Added Mode 7 freeform note — genre-agnostic, never affects mastery thresholds, always available
- The Blend Problem: Added "use Mode 7 freeform for assets outside any genre"
- Footer: v1.0 → v1.1

### v1.2 — Version Alignment
- No content changes. PROPOSED_CHANGES_001 session did not affect this document. Version incremented from v1.1 to v1.2 to maintain Bible-wide version consistency per Document Hygiene Rules.

### v1.3 — Changelog Added
- CHANGE-018: Changelog section added to document
- Version corrected from v1.2 to v1.3 to align with all other Bible documents
- Footer: v1.1 → v1.3

---

## am-pixel/README.md (intra-folder hub)

### v1.2 — Created (new file)
- Document index table with read order for all 5 documents
- One-paragraph product description
- Seven generation modes summary table (including Mode 5b)
- Quality standard summary (both thresholds with correct definitions)
- Key architecture decisions quick reference (token space, generation order, hardware, three rubrics, known risks)
- Genre scope summary
- Reason: CHANGE-006 identified that navigating directly into am-pixel/ had no orientation document

### v1.3 — Speed vs. Accuracy & Architecture Updates
- Added "On Speed vs. Accuracy — A Design Position Statement" section — explicit documented response to recurring speed concern raised by multiple external reviewers; direct OpenClaw directive included prohibiting speed-motivated architecture changes without human approval
- Key Architecture Decisions updated: added 2D positional encoding (CHANGE-010), rubric scoring split — automated 85pts / human 15pts (CHANGE-013), multi-view generation conditioning on DNA + Brief + Master View Tokens (CHANGE-016)
- CHANGE-018: Changelog section added
- Footer: v1.2 → v1.3

### v1.3 — 2026-04-19 Hygiene (no spec delta)
- Changelog entry added for working-tree alignment: repo umbrella README, archive folder names, `SPEC`/hub version parity

### v1.4 — 2026-04-19
- Bible **v1.4**: hub title and changelog synchronized; footer **v1.3 → v1.4**
- Document index table: added `BIBLE_CHANGELOG.md`, `PROPOSED_CHANGES_001.md`, `PROPOSED_CHANGES_002.md` with read-order hints

---

## am-pixel/BIBLE_CHANGELOG.md (this document)

### v1.0 — Compiled Retroactively
- Created to reconstruct complete change history from project conversation history
- Covered documents: ROOT README, SPEC, ROADMAP, OPENCLAW_PROMPT, FOLDER_STRUCTURE, GENRE_TAXONOMY, am-pixel/README, logs/, PROPOSED_CHANGES
- History compiled through Bible v1.2
- Document Hygiene Rules established for going forward

### v1.1 — v1.3 Session Added
- Added v1.3 entries for all documents covering PROPOSED_CHANGES_002 implementation
- Corrected GENRE_TAXONOMY retroactive history (v1.2 was a version alignment only, not a content change)
- Corrected am-pixel/README history (created at v1.2, not v1.1)
- Document Hygiene Rules preserved and referenced

### v1.2 — 2026-04-19 Document hygiene pass
- This file’s header/footer metadata aligned to Bible **v1.3**; ROOT README Status synced to v1.3; archive folder names aligned to Bible lineage

### v1.3 — 2026-04-19 Bible v1.4 alignment
- Header/footer and version convention list set to **v1.4**; ROOT README Status updated to **v1.4**; archive path **`bible-v1.4`**; meta-entry documents hygiene numbering (no new CHANGE series)

---

## am-pixel/logs/ (all files)

### v1.2 — All Created (new directory)

**hardware.log** — placeholder with format documentation (backend, GPU model, VRAM, baseline inference speed)

**generation_log.md** — placeholder with table header (date, asset, mode, score, result, notes)

**rebuild_log.md** — placeholder with table header (date, asset, rebuild #, failure points, root cause, resolution)

**training_log.md** — placeholder with structured sections for each Phase 4 architecture experiment: structure-aware vs raster comparison, sequence length evaluation, DNA conditioning consistency measurement, training runs table

**evaluation.log** — placeholder with table header (date, test type, engine score, human score, delta, notes)

**errors.log** — placeholder with header comment

**BLOCKERS.md** — placeholder with table header (date, phase, task, attempted, options, status)

**phase_gates.md** — pre-populated with all Phase 0–8 gate checklists and evidence fields

---

## PROPOSED_CHANGES.md (Series 001 — archived)

### v0.1 — Created and Evaluated
All changes accepted and integrated into Bible v1.2:
- CHANGE-001: Structure-aware generation order + REFINEMENT-001A (transparent pixel category)
- CHANGE-002: Prompt expansion layer + REFINEMENT-002A (SNES style-bible guardrails)
- CHANGE-003: GPU backend universalization + REFINEMENT-003A (inference speed benchmark in hardware log)
- CHANGE-004: SPEC.md structural fixes (section 6 header, section 13 numbering gap)
- CHANGE-005: OPENCLAW_PROMPT fixes (named document list, forced confirmation) + REFINEMENT-005A (architecture confirmation)
- CHANGE-006: Folder structure additions (am-pixel/README.md, initialized logs, detector.py)
- CHANGE-007: Sequence length and error accumulation (Risk A)
- CHANGE-008: DNA conditioning architecture decision (Risk B)
- CHANGE-009: Animation temporal coherence gap (Risk C)

Status: Fully implemented. Document archived.

---

## PROPOSED_CHANGES_002.md (Series 002 — archive)

### v0.1 — Initial Batch
- CHANGE-010: 2D positional encodings
- CHANGE-011: MaskGIT as Phase 4 architectural experiment
- CHANGE-012: Sliding window conditioning for tileset generation
- CHANGE-013 + REFINEMENT-013A: Automated/human rubric decoupling; context-aware Soul scoring
- CHANGE-014: Pixel classifier simplification for foundation training
- CHANGE-015: Skeletal pose tokens as animation upgrade path
- CHANGE-016: Brief as feature inventory; twin input for multi-view generation (Backpack Problem)
- CHANGE-017: Paired view training sequences
- CHANGE-018: Document changelogs

### v0.2 — Second Batch
- CHANGE-019: Golden Dataset strategy for Phase 3
- CHANGE-020: OpenClaw architecture review gate for core model files
- CHANGE-021: VLM critic as evaluation engine upgrade path
- CHANGE-022: Component compositing as post-MVP architecture evolution

### v0.3 — Third Batch (Legal & Community)
- CHANGE-023: Training data provenance manifest (legal protection)
- CHANGE-024: Community contributor program (human-only initiative — OpenClaw must not act on this)

Status: All changes (CHANGE-010 through CHANGE-023) implemented into Bible v1.3 content revision; subsequently numbered as Bible **v1.4** (2026-04-19 alignment pass — no additional CHANGE deltas). CHANGE-024 is documented for human consideration only — no implementation required.

---

## PROPOSED_CHANGES_003.md (Series 003 — archive)

### v0.2 — Drift prevention & compliance
- CHANGE-025: CONSTITUTION.md (nine rules)
- CHANGE-026: Session Startup Protocol → session_log.md
- CHANGE-027: decision_log.md
- CHANGE-028: compliance.py, dna_lock_verifier.py, rubric evidence, pre-commit hook, mode docstrings
- CHANGE-029: DNA rollback procedure; versioned DNA filenames
- CHANGE-030: Hardware Reality table; SPEC §14 CPU clarification
- CHANGE-031: Phase 8 failure cluster analysis + three-cycle escalation
- REFINEMENT-025A: Continuous Training re-anchor (§9.3)

Status: Merged into Bible v1.5. Document retained as proposal archive.

---

---

## PROPOSED_CHANGES_004.md (Series T — Transformative Branch — never merged to main)

### v0.1 — Transformative Branch Governance
- **CHANGE-T01:** `TRANSFORMATIVE_BRANCH_NOTICE.md` (repo root) — hard boundary document: no merge, no weight distribution, no output crossover. Also added as Constitution Rule 10.
- **CHANGE-T02:** License allowlist suspended on transformative branch for entries to `TRAINING_PROVENANCE_MANIFEST.transformative.json`. Entry-before-write and never-delete rules unchanged. `copyright_filter_passed` field retained as observation. SPEC §3.2 Tier 2 addendum, SPEC §15 transformative addendum, OPENCLAW_PROMPT Training Data addendum, ROADMAP Phase 3 Tier 2 annotation, CONSTITUTION Rule 5 addendum.
- **CHANGE-T03:** Parallel paths added to FOLDER_STRUCTURE.md: `TRAINING_PROVENANCE_MANIFEST.transformative.json`, `corpus_transformative/train/`, `corpus_transformative/validation/`, `data/scraper/sources_transformative.md`, `data/scraper/scrape_log_transformative.md`, `logs/transformative_log.md`. ROADMAP Phase 0 init task added for transformative paths.
- **CHANGE-T04:** Branch-aware compliance gates added to `tools/compliance.py`: `transformative_provenance_gate()` and `training_run_gate_transformative()`. Existing canonical gates unchanged. Tests added in `test_compliance.py`. Pre-commit banner updated. Scraper and validator docstrings updated to reference `--transformative` flag contract.
- **CHANGE-T05:** Explicit table of rules preserved unchanged on this branch — documented in `PROPOSED_CHANGES_004.md` for future-session clarity.
- **CHANGE-T06:** Constitution Rule 11 — Protected Files. Added to CONSTITUTION.md, compliance.py (`constitution_integrity_gate()`), git-hooks/pre-commit (shell-level block), OPENCLAW_PROMPT.md Startup Protocol (step 0), and test_compliance.py (4 new tests). Pre-commit hook now blocks commits staging any protected file; gate runs at session start before any other action. Applies to both branches (on main this is CHANGE-032).

Status: Implemented on transformative branch. This entry and the T-series are transformative-branch-only — they must never appear in main's BIBLE_CHANGELOG.md.

---

## Document Hygiene Rules (Going Forward)

1. Every change to any Bible document gets an entry in this file first
2. Changelog entries must specify: what changed, which document and section, and why
3. Version numbers increment on every edit session — no silent changes
4. All Bible documents must share the same version number after any update session (ROOT README tracks separately as the umbrella document)
5. The PROPOSED_CHANGES staging document pattern works well — use it for future batches before committing to the Bible
6. When an external AI evaluates the Bible, log the evaluation source and any accepted changes here
7. Never update a single document in isolation — always check for cross-reference impacts and update all affected documents in the same pass
8. PROPOSED_CHANGES documents are archived (not deleted) once fully implemented

---

*AM Pixel Bible Changelog v1.5 | Absentmind Studio*
*v1.0 compiled retroactively | ongoing entries in real time*
