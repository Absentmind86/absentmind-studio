# AM Pixel — Project Folder Structure
**Absentmind Studio | Version 1.0**

OpenClaw initializes this exact structure in Phase 0. Every directory and file listed here must exist before Phase 1 begins. Placeholder files use `.gitkeep`.

---

```
am-pixel/
│
├── README.md                          ← Links to all spec documents
├── SPEC.md                            ← Full technical specification
├── ROADMAP.md                         ← Phased execution plan
├── GENRE_TAXONOMY.md                  ← Genre tiers and mastery definitions
├── FOLDER_STRUCTURE.md                ← This document
├── OPENCLAW_PROMPT.md                 ← Prompt for OpenClaw initialization
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
│   ├── architecture/
│   │   ├── transformer.py             ← Core model architecture (PyTorch)
│   │   ├── conditioning.py            ← DNA conditioning encoder
│   │   ├── tokenizer.py               ← Palette index tokenizer
│   │   └── config.py                  ← Model hyperparameters
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
│   │   ├── scraper.py                 ← Source scraping and downloading
│   │   ├── sources.md                 ← Documented data sources with license status
│   │   └── scrape_log.md              ← Log of all scraping runs
│   ├── pipeline/
│   │   ├── extractor.py               ← Sprite extraction from sprite sheets
│   │   ├── indexer.py                 ← RGB → palette index conversion
│   │   ├── validator.py               ← SNES palette compliance validation
│   │   ├── metadata.py                ← Metadata tagging for training pairs
│   │   └── splitter.py                ← Train/validation split
│   ├── corpus/                        ← Processed training data
│   │   ├── train/                     ← Training split
│   │   │   └── .gitkeep
│   │   └── validation/                ← Validation split
│   │       └── .gitkeep
│   ├── antipatterns/                  ← Intentionally bad sprites for evaluation calibration
│   │   ├── generator.py               ← Programmatic bad sprite generator
│   │   └── labeled/                   ← Bad sprite + corrected version pairs
│   │       └── .gitkeep
│   └── corpus_stats.md                ← Corpus statistics log
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
│   │   └── adjustment_handler.py      ← Applies adjustment requests as deltas
│   ├── modes/
│   │   ├── mode1_character.py         ← Character creation mode
│   │   ├── mode2_extension.py         ← Sprite sheet extension mode
│   │   ├── mode3_tileset.py           ← Environment and tileset generation mode
│   │   ├── mode4_ui.py                ← UI generation mode
│   │   └── mode5_font.py              ← Font generation mode
│   ├── github_integration.py          ← GitHub repo read/write and DNA scan
│   └── project_manager.py             ← Project state, tab organization, session management
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
├── practice/                          ← Practice Gauntlet output (not production)
│   ├── characters/
│   │   └── .gitkeep
│   ├── antipattern_library/           ← Generated bad examples for evaluation calibration
│   │   └── .gitkeep
│   └── gauntlet_report.md             ← Gauntlet results and lessons
│
├── logs/                              ← System operation logs
│   ├── generation_log.md              ← Log of every generation attempt with scores
│   ├── rebuild_log.md                 ← Log of every rebuild with root cause
│   ├── training_log.md                ← Training run summaries
│   ├── BLOCKERS.md                    ← Documented blockers awaiting human input
│   └── phase_gates.md                 ← Record of phase gate completions
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
├── requirements_cuda.txt              ← CUDA-specific dependencies
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

*AM Pixel Folder Structure v1.0 | Absentmind Studio*
