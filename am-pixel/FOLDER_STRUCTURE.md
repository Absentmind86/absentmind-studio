# AM Pixel — Project Folder Structure
**Absentmind Studio | Version 1.4**

OpenClaw initializes this exact structure in Phase 0. Every directory and file listed here must exist before Phase 1 begins. Placeholder files use `.gitkeep`.

---

```
am-pixel/
│
├── README.md                          ← Links to all spec documents; orientation hub for OpenClaw
├── SPEC.md                            ← Full technical specification
├── ROADMAP.md                         ← Phased execution plan
├── GENRE_TAXONOMY.md                  ← Genre tiers and mastery definitions
├── FOLDER_STRUCTURE.md                ← This document
├── OPENCLAW_PROMPT.md                 ← Prompt for OpenClaw initialization
├── BIBLE_CHANGELOG.md                 ← Complete authoritative change history for all Bible documents; log changes here before applying to any document
├── PROPOSED_CHANGES_002.md            ← Series 002 archive — substantive items (CHANGE-010–023) merged into Bible; document retained for rationale and review history
│
├── knowledge/                         ← Boot Training knowledge base
│   ├── HARDWARE_CONSTRAINTS.md        ← SNES + 5 other platforms
│   ├── PIXEL_ART_THEORY.md            ← 20+ universal principles
│   ├── MISTAKE_TAXONOMY.md            ← Failure modes + corrective principles
│   ├── EVALUATION_RUBRIC.md           ← Scoring criteria (95+ to pass)
│   ├── REFERENCE_GAMES.md             ← 40+ games with annotated analysis
│   ├── RESOURCE_LIBRARY.md            ← Studied resources with quality ratings
│   └── LESSONS_LEARNED.md             ← Growing rulebook from production experience
│
├── style-bible/                       ← Locked project-wide visual constraints
│   ├── MASTER_PALETTE.md              ← Full project palette with ramp families
│   ├── PROPORTION_SYSTEM.md           ← Canonical sprite dimensions per context
│   ├── ANIMATION_STANDARD.md          ← Required animation sets and frame counts
│   └── LIGHTING_STANDARD.md           ← Light source and environmental lighting rules
│
├── model/                             ← Custom transformer model
│   ├── hardware/
│   │   └── detector.py                ← GPU/backend detection utility — ALL device references route through here. Built in Phase 0.
│   ├── architecture/
│   │   ├── transformer.py             ← Core model architecture (PyTorch)
│   │   ├── conditioning.py            ← DNA conditioning encoder (prefix method; cross-attention upgrade path documented in SPEC §3.4)
│   │   ├── tokenizer.py               ← Palette index tokenizer — outputs (palette_index, canvas_x, canvas_y) tuples; 2D positional encodings
│   │   ├── config.py                  ← Model hyperparameters
│   │   ├── IMPLEMENTATION_NOTES.md    ← Written by OpenClaw after building architecture files; human review required before any training run (CHANGE-020)
│   │   └── COMPONENT_COMPOSITING_NOTES.md ← Post-MVP architecture reference — component/layer-based generation future direction (CHANGE-022)
│   ├── training/
│   │   ├── train.py                   ← Main training loop
│   │   ├── finetune.py                ← Fine-tuning loop
│   │   ├── dataset.py                 ← Dataset class and data loading
│   │   ├── loss.py                    ← Loss functions
│   │   └── scheduler.py               ← Learning rate scheduling
│   ├── inference/
│   │   ├── generate.py                ← Sprite generation from DNA + prompt
│   │   ├── server.py                  ← FastAPI local inference server
│   │   └── api.py                     ← Inference API endpoints
│   ├── checkpoints/                   ← Model checkpoint saves
│   │   └── .gitkeep
│   └── logs/                          ← Training logs
│       └── .gitkeep
│
├── data/                              ← Training data pipeline
│   ├── scraper/
│   │   ├── scraper.py                 ← Source scraping and downloading — writes provenance entry before writing sprite
│   │   ├── sources.md                 ← Documented data sources with license status
│   │   └── scrape_log.md              ← Log of all scraping runs
│   ├── pipeline/
│   │   ├── extractor.py               ← Sprite extraction from sprite sheets
│   │   ├── indexer.py                 ← RGB → palette index conversion
│   │   ├── pixel_classifier.py        ← Classifies each pixel as transparent/outline/structural/non-structural (four-category for Stage 1; --full-five-category flag for Stage 2)
│   │   ├── sequence_reorderer.py      ← Reorders token sequences with positional encoding preservation — outputs (palette_index, canvas_x, canvas_y) tuples
│   │   ├── view_pair_detector.py      ← Identifies candidate view pairs within sprite sheets using palette similarity and proportion matching (CHANGE-017)
│   │   ├── pair_annotator.py          ← Presents view pair candidates for human confirmation; writes confirmed pairs with view_pair_id (CHANGE-017)
│   │   ├── pose_extractor.py          ← STUB — documented interface only. Extracts simplified 2D skeleton key points from sprites for animation temporal conditioning upgrade path (CHANGE-015)
│   │   ├── validator.py               ← SNES palette compliance validation — checks for provenance entry before passing sprite
│   │   ├── metadata.py                ← Metadata tagging for training pairs
│   │   └── splitter.py                ← Train/validation split
│   ├── golden/                        ← Tier 1 — manually curated Golden Dataset (3,000–5,000 sprites, human-verified)
│   │   ├── CONTRIBUTORS.md            ← Human record of Golden Dataset contributors: handle, anonymity preference, accepted sprites, tier
│   │   ├── curation_log.md            ← Per-sprite curation record — source, extraction method, reviewer (CHANGE-019)
│   │   └── .gitkeep
│   ├── corpus/                        ← Tier 2 — broad scraped corpus
│   │   ├── train/                     ← Training split
│   │   │   └── .gitkeep
│   │   └── validation/                ← Validation split
│   │       └── .gitkeep
│   ├── antipatterns/                  ← Intentionally bad sprites for evaluation calibration
│   │   ├── generator.py               ← Programmatic bad sprite generator
│   │   └── labeled/                   ← Bad sprite + corrected version pairs
│   │       └── .gitkeep
│   ├── TRAINING_PROVENANCE_MANIFEST.json  ← IMMUTABLE LEGAL LEDGER — initialized as [] in Phase 0, never deleted. Every training sprite logged with source, license, pHash, tier. (CHANGE-023)
│   └── corpus_stats.md                ← Corpus statistics log — reports Tier 1 and Tier 2 separately
│
├── tools/                             ← Evaluation and management tooling
│   ├── palette_validator.py           ← Checks sprite against palette constraints
│   ├── dna_diff.py                    ← Visual diff of sprite vs DNA specification
│   ├── dna_extractor.py               ← Extracts DNA JSON from approved sprite
│   ├── rubric_scorer.py               ← Selects correct rubric (A/B/C) by asset type, returns score breakdown
│   ├── banding_detector.py            ← Detects horizontal/vertical color banding
│   ├── outline_checker.py             ← Identifies pure black outlines (must be local color)
│   ├── anti_aliasing_detector.py      ← Flags sub-pixel blending (not allowed in SNES style)
│   ├── seam_validator.py              ← Tests all four edges of tiles for seamless tiling
│   ├── tileset_anchor_extractor.py    ← Derives Tileset Anchor from approved seed tiles
│   ├── layer_compositor.py            ← Assembles parallax layers at scroll offsets for evaluation
│   ├── effect_timing_evaluator.py     ← Evaluates battle effect timing and weight at playback speed
│   ├── icon_grammar_checker.py        ← Validates icon set visual consistency within categories
│   ├── sheet_manager.py               ← Non-destructive sprite sheet operations
│   ├── comparison_sheet.py            ← Generates side-by-side project character comparison
│   ├── continuity_checker.py          ← Runs all three continuity checks
│   ├── vlm_critic.py                  ← STUB — documented interface only. VLM-based semantic evaluation for contextually ambiguous rubric criteria; only invoked on borderline automated failures (CHANGE-021)
│   └── export/
│       ├── godot_exporter.py          ← Godot SpriteFrames resource export
│       ├── rpgmaker_exporter.py       ← RPG Maker MZ format export
│       ├── gamemaker_exporter.py      ← GameMaker format export
│       └── generic_exporter.py        ← Generic PNG + JSON manifest export
│
├── pipeline/                          ← AM Pixel application pipeline
│   ├── approval/
│   │   ├── conversation.py            ← Natural language approval loop
│   │   ├── presenter.py               ← Candidate presentation (1x and 4x zoom)
│   │   ├── adjustment_handler.py      ← Applies adjustment requests as deltas
│   │   └── prompt_expander.py         ← Optional character brief expansion (Mode 5b) — LLM API call with SNES style-bible guardrails
│   ├── modes/
│   │   ├── mode1_character.py         ← Character creation mode
│   │   ├── mode2_extension.py         ← Sprite sheet extension mode
│   │   ├── mode3_tileset.py           ← Environment and tileset generation mode
│   │   ├── mode3b_parallax.py         ← Parallax background generation mode
│   │   ├── mode4_ui.py                ← UI generation mode
│   │   ├── mode5_font.py              ← Font generation mode
│   │   ├── mode6_effects.py           ← Battle effect animation mode
│   │   └── mode7_freeform.py          ← Freeform generation (no DNA, no style constraints, any resolution)
│   ├── github_integration.py          ← GitHub repo read/write and DNA scan
│   └── project_manager.py             ← Project state, tab organization, session management
│
├── ui/                                ← Full local web interface
│   ├── app.py                         ← FastAPI entrypoint — serves both inference API and web UI
│   ├── templates/                     ← HTML templates
│   │   ├── index.html                 ← Main application shell
│   │   ├── project_tabs.html          ← Project asset tab structure
│   │   └── freeform.html              ← Freeform generation tab
│   └── static/                        ← CSS and JS assets
│       ├── main.css
│       └── main.js
│
├── projects/                          ← User game projects (one folder per project)
│   └── .gitkeep
│
├── dna/                               ← Character DNA store
│   ├── CONTINUITY_MANIFEST.md         ← Master continuity tracking document
│   └── characters/                    ← One JSON file per approved character
│       └── .gitkeep
│
├── sheets/                            ← Sprite sheet layout manifests
│   └── .gitkeep                       ← One JSON manifest per sprite sheet
│
├── assets/                            ← Generated and approved game assets
│   ├── characters/                    ← Organized by character name
│   │   └── .gitkeep
│   ├── enemies/
│   │   └── .gitkeep
│   ├── battle_effects/
│   │   ├── projectile/
│   │   │   └── .gitkeep
│   │   ├── area/
│   │   │   └── .gitkeep
│   │   ├── status/
│   │   │   └── .gitkeep
│   │   ├── healing/
│   │   │   └── .gitkeep
│   │   ├── elemental/
│   │   │   └── .gitkeep
│   │   ├── summon/
│   │   │   └── .gitkeep
│   │   ├── hit_impact/
│   │   │   └── .gitkeep
│   │   └── death/
│   │       └── .gitkeep
│   ├── tilesets/
│   │   ├── towns/
│   │   │   └── .gitkeep
│   │   ├── dungeons/
│   │   │   └── .gitkeep
│   │   ├── castles/
│   │   │   └── .gitkeep
│   │   ├── caves/
│   │   │   └── .gitkeep
│   │   ├── wilderness/
│   │   │   └── .gitkeep
│   │   └── world_map/
│   │       ├── tiles/
│   │       │   └── .gitkeep
│   │       └── location_markers/
│   │           └── .gitkeep
│   ├── parallax/
│   │   └── .gitkeep
│   ├── ui/
│   │   ├── hud/
│   │   │   └── .gitkeep
│   │   ├── menus/
│   │   │   └── .gitkeep
│   │   ├── dialogue/
│   │   │   └── .gitkeep
│   │   ├── inventory/
│   │   │   └── .gitkeep
│   │   ├── item_icons/
│   │   │   └── .gitkeep
│   │   ├── status_icons/
│   │   │   └── .gitkeep
│   │   ├── element_icons/
│   │   │   └── .gitkeep
│   │   └── title_screen/
│   │       └── .gitkeep
│   └── fonts/
│       └── .gitkeep
│
├── freeform/                          ← Standalone freeform (Mode 7) outputs — not project assets
│   └── .gitkeep
│
├── practice/                          ← Practice Gauntlet output (not production)
│   ├── characters/
│   │   └── .gitkeep
│   ├── antipattern_library/           ← Generated bad examples for evaluation calibration
│   │   └── .gitkeep
│   └── gauntlet_report.md             ← Gauntlet results and lessons
│
├── logs/                              ← System operation logs — ALL initialized as empty placeholder files in Phase 0
│   ├── hardware.log                   ← Hardware detection result: GPU model, VRAM, backend, baseline inference speed
│   ├── generation_log.md              ← Log of every generation attempt with scores
│   ├── rebuild_log.md                 ← Log of every rebuild with root cause
│   ├── training_log.md                ← Training run summaries + architecture experiment results
│   ├── evaluation.log                 ← Evaluation engine accuracy tracking
│   ├── errors.log                     ← Runtime errors and stack traces
│   ├── freeform_log.md                ← Log of all Mode 7 freeform generation outputs (reference only — not project assets)
│   ├── BLOCKERS.md                    ← Documented blockers awaiting human input
│   └── phase_gates.md                 ← Record of phase gate completions with evidence
│
├── tests/                             ← Automated tests for all tooling
│   ├── test_palette_validator.py
│   ├── test_dna_extractor.py
│   ├── test_rubric_scorer.py
│   ├── test_sheet_manager.py
│   ├── test_continuity_checker.py
│   └── test_export.py
│
├── requirements.txt                   ← Python dependencies
├── requirements_hardware.txt          ← Hardware-specific dependencies (CUDA/ROCm/MPS variants)
└── .env.example                       ← Environment variable template (no secrets)
```

---

## File Naming Conventions

**DNA files:** `dna/characters/[character_id].json`
Example: `dna/characters/sam_vendor.json`

**Sheet manifests:** `sheets/[character_id]_[profile].json`
Example: `sheets/sam_vendor_world.json`

**Sprite sheets:** `assets/characters/[character_id]/[profile].png`
Example: `assets/characters/sam_vendor/world.png`

**Tileset sheets:** `assets/tilesets/[category]/[tileset_id].png`
Example: `assets/tilesets/towns/port_town_rainy.png`

**Character IDs:** lowercase, underscores, no spaces
Example: `lighthouse_keeper`, `sam_vendor`, `dark_mage_boss`

---

## Git Commit Convention

```
Phase N complete: [description]
DNA locked: [character_name] v[N]
Sheet extended: [character_name] — [animation_name] ([N] frames)
Tileset approved: [tileset_id]
Training checkpoint: step [N], val_loss [X.XXX]
Fine-tune complete: pass rate [N]/100
Phase gate: [gate_name] passed
BLOCKER: [short description] — awaiting human input
```

---

*AM Pixel Folder Structure v1.4 | Absentmind Studio*

---

## Changelog

### v1.3 — 2026-04-12
- **CHANGE-017:** data/pipeline/ — added view_pair_detector.py (identifies candidate view pairs within sprite sheets via palette similarity and proportion heuristics) and pair_annotator.py (presents candidates for human confirmation, writes confirmed pairs with view_pair_id and direction labels).
- **CHANGE-015:** data/pipeline/ — added pose_extractor.py stub. Documented interface only — extracts simplified 2D skeleton key points from sprites for animation temporal conditioning upgrade path. Only implemented if raw-token temporal conditioning fails.
- **CHANGE-019:** data/ — added golden/ directory as Tier 1 manually curated Golden Dataset storage (3,000–5,000 sprites, human-verified). Added data/golden/CONTRIBUTORS.md — human record of Golden Dataset contributors with handle, anonymity preference, accepted sprite count, tier.
- **CHANGE-023:** data/ — added TRAINING_PROVENANCE_MANIFEST.json. Initialized as empty array in Phase 0. Immutable legal ledger recording source URL, creator, license, pHash, and tier for every training sprite. Never deleted. Scraper writes entry before writing sprite.
- **CHANGE-023:** corpus_stats.md description updated — must report Tier 1 and Tier 2 statistics separately.
- **CHANGE-021:** tools/ — added vlm_critic.py stub. Documented interface only — VLM-based semantic evaluation for contextually ambiguous rubric criteria. Only invoked on borderline automated failures; returns structured JSON. Implemented Phase 5 only if false positive rates warrant it.
- **CHANGE-020:** model/architecture/ — added IMPLEMENTATION_NOTES.md. Written by OpenClaw after building architecture files; documents every implementation decision (2D positional encodings, DNA conditioning, causal mask). Human review required and explicit approval must be received before any training run begins.
- **CHANGE-022:** model/architecture/ — added COMPONENT_COMPOSITING_NOTES.md stub. Post-MVP architecture reference documenting component/layer-based generation as future direction for the Backpack Problem and character customization.
- **CHANGE-014:** data/pipeline/pixel_classifier.py description updated — four-category classification default (transparent, outline, structural, non-structural); `--full-five-category` flag for fine-tuning stage where data quality is controlled.
- **CHANGE-010:** model/architecture/tokenizer.py description updated — outputs (palette_index, canvas_x, canvas_y) tuples; 2D positional encodings (learned X + Y coordinate embeddings summed at input layer).
- **CHANGE-018:** Changelog section added.
- Added `BIBLE_CHANGELOG.md` and `PROPOSED_CHANGES_002.md` to top-level file listing — these are meta-documents that exist in the repo and must be visible to OpenClaw.
- Added missing `logs/freeform_log.md` to logs directory listing — referenced in SPEC §5.7 but previously absent from folder structure.

### v1.4 — 2026-04-19
- Bible **v1.4**: per Document Hygiene Rules, synchronized with all other Bible documents; archive folder **`bible-v1.4`** (no folder-tree delta in this entry).
- **CHANGE-019:** `data/golden/curation_log.md` added to tree — per-sprite Golden Dataset curation record (was specified in Series 002 but missing from listing).
- **Series 002:** Phase 0 scaffold created on disk for all listed paths (Python stubs, UI placeholders, `TRAINING_PROVENANCE_MANIFEST.json`, logs, tests, requirements). `PROPOSED_CHANGES_002.md` header updated to archive/merged status.

### v1.2 — 2026-04-11
- **CHANGE-003:** model/ — added hardware/ subdirectory with detector.py. All device references throughout codebase must route through this utility. No hardcoded "cuda" strings anywhere.
- **CHANGE-003:** model/architecture/conditioning.py — comment updated to reference cross-attention upgrade path documented in SPEC §3.4 Risk B.
- **CHANGE-001:** model/architecture/tokenizer.py — comment updated to document structure-aware ordering (transparent→outline→fill→shade→detail).
- **CHANGE-001:** data/pipeline/ — added pixel_classifier.py (classifies each pixel into five structural categories for structure-aware ordering).
- **CHANGE-001:** data/pipeline/ — added sequence_reorderer.py (reorders token sequences with positional encoding preservation).
- **CHANGE-002:** pipeline/approval/ — added prompt_expander.py (Mode 5b LLM expansion call with SNES style-bible guardrails, genre-aware system prompt).
- logs/ section expanded — all files now initialized as placeholder files in Phase 0: hardware.log (backend, GPU model, VRAM, baseline inference speed), evaluation.log, errors.log, generation_log.md, rebuild_log.md, training_log.md (with structured sections for Phase 4 architecture experiments), BLOCKERS.md, phase_gates.md (pre-populated with all Phase 0–8 gate checklists).
- requirements_cuda.txt renamed to requirements_hardware.txt to reflect universal backend support.

### v1.1 — 2026-04-11
- pipeline/modes/ — added mode6_effects.py and mode7_freeform.py.
- pipeline/ — added mode3b_parallax.py.
- ui/ directory added as new top-level: app.py (FastAPI entrypoint), templates/ (index.html, project_tabs.html, freeform.html), static/ (main.css, main.js).
- assets/ — added battle_effects/ with 8 subcategories: projectile/, area/, status/, healing/, elemental/, summon/, hit_impact/, death/.
- assets/tilesets/world_map/ — split into tiles/ and location_markers/ subdirectories.
- assets/ui/ — added item_icons/, status_icons/, element_icons/, title_screen/.
- freeform/ directory added at root level for standalone Mode 7 outputs (never project assets).

### v1.0 — Original Release
- Complete directory tree for am-pixel/ project established.
- model/ with architecture/, training/, inference/, checkpoints/, logs/.
- data/ with scraper/, pipeline/, corpus/, antipatterns/.
- tools/ with evaluation and management scripts (palette_validator, dna_diff, rubric_scorer, etc.).
- pipeline/ with approval/, modes/ (mode1–5 at this version), github_integration, project_manager.
- projects/, dna/, sheets/, assets/ (characters, enemies, tilesets, parallax, ui, fonts), practice/, logs/, tests/.
- requirements.txt, requirements_cuda.txt, .env.example.
- File naming conventions section established.
- Git commit convention section established.
