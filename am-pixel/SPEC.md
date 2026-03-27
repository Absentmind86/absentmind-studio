# AM Pixel — Full Technical Specification
**Absentmind Studio | Version 1.1**

---

## 1. Product Definition

AM Pixel is a purpose-built AI sprite generator and game asset manager for retro-style pixel art games. It produces original, studio-quality pixel art assets through natural language conversation, with a character DNA system that enforces perfect visual continuity across all assets in a project. It also includes a freeform generation mode for arbitrary custom pixel art images not bound to any project DNA, style bible, or SNES constraints.

AM Pixel is not a wrapper around Stable Diffusion, Midjourney, or any existing image generation model. It is a custom-built autoregressive transformer that generates sprites natively in palette-index space — the same way a language model generates tokens. This architecture is the core innovation that makes pixel-perfect DNA enforcement possible.

---

## 2. Quality Standard

The quality target is work that a pixel art expert cannot reliably distinguish from professional SNES-era studio output. This is not aspirational — it is the shipping standard. Assets that do not meet this bar are not presented to the user.

**Individual sprite passing threshold: 95/100 on the AM Pixel evaluation rubric.**
**Model production threshold: See batch pass rate definition below.**

---

### ⚠️ CRITICAL DEFINITION — BATCH PASS RATE vs SCORE

These are two completely different measurements. Read this before proceeding.

**The 95/100 threshold** is a SCORE. Each individual sprite is evaluated on the rubric and must earn a score of 95 points or higher out of 100 to pass. A sprite that scores 94 fails. A sprite that scores 95 passes.

**The 99/100 production threshold** is a BATCH PASS RATE. It is NOT a score of 99 points.

It means: **in a validation batch of 100 generated sprites, a minimum of 99 individual sprites must each independently score 95 or above on the evaluation rubric.**

Examples to make this unambiguous:

- 99 sprites each scoring 95+ → PRODUCTION THRESHOLD MET ✅
- 100 sprites each scoring 94 → PRODUCTION THRESHOLD NOT MET ❌ (none pass the 95 individual threshold)
- 1 sprite scoring 99 points → PRODUCTION THRESHOLD NOT MET ❌ (only 1 sprite evaluated, need 99 passing out of 100)
- 98 sprites scoring 100 points → PRODUCTION THRESHOLD NOT MET ❌ (98 pass, need minimum 99)

Every time this document uses the phrase "99/100 production threshold" it means this batch pass rate. It never refers to a point score of 99.

Until this batch pass rate is achieved, the model is not in production. It is still training.

---

## 3. Core Architecture

### 3.1 The Model

AM Pixel's generation engine is a purpose-built autoregressive transformer with the following characteristics:

**Native palette-index tokenization:**
Sprites are not generated as RGB images. They are generated as sequences of palette index tokens. A 16x24 sprite is a sequence of 384 tokens. Each token is an index into the character's locked palette — not a color value. This makes palette enforcement exact and deterministic, not approximate.

**Why this matters:**
Diffusion-based models generate in RGB color space with probabilistic sampling. Every generation is a slightly different sample. Over a sprite sheet of 40 frames, subtle color drift accumulates into visible inconsistency. The autoregressive token approach generates the same palette index when conditioned on the same DNA — consistency is structural, not enforced after the fact.

**Conditioning inputs:**
The model is conditioned on structured DNA specifications at generation time. DNA is not a hint — it collapses the valid token space. The model cannot generate a color that isn't in the character's palette because those token indices don't exist in the conditioned vocabulary.

**For Mode 7 freeform generation:** Conditioning tokens are omitted entirely. The vocabulary expands to the full 256-color palette. The SNES style constraints and DNA enforcement are suspended. Freeform outputs are PNG only and are never added to the continuity manifest or DNA store.

**Architecture specifics:**
- Transformer decoder architecture (GPT-style)
- Sequence length: sprite width × height (e.g., 384 for 16x24)
- Vocabulary: project palette indices (max 256 for full SNES palette, typically 15 per character)
- Conditioning: structured DNA JSON prepended as context tokens
- Training objective: next-token prediction on palette-index sequences
- Hardware target: NVIDIA GPU with CUDA, minimum 10GB VRAM

### 3.2 The Training Pipeline

The model is trained in two stages:

**Stage 1 — Foundation training:**
Large corpus of indexed pixel art sprites across multiple hardware platforms and genres. Teaches the model fundamental pixel art construction — palette relationships, proportion conventions, outline technique, shading principles. This is not style imitation — it is principle extraction.

**Stage 2 — Quality fine-tuning:**
Curated high-quality subset. Only sprites that pass the evaluation rubric. Teaches the model to weight its generations toward quality output. Continuously updated as production generates new approved assets.

**Training data sourcing priority:**
1. Permissively licensed sprite archives (OpenGameArt.org, itch.io free packs)
2. Community-contributed pixel art repositories
3. Broader sprite corpus from public archives
4. Approved production assets from AM Pixel users (opt-in, anonymized)

### 3.3 System Components

| Component | Responsibility |
|-----------|----------------|
| Training Engine | Self-directed research, corpus curation, model training, quality fine-tuning |
| Generation Engine | Custom transformer inference — produces sprite candidates from DNA + prompt |
| Freeform Engine | Unconstrained generation mode — bypasses DNA and style bible, uses full 256-color vocabulary, any resolution, outputs PNG only. See Mode 7. |
| Evaluation Engine | Scores every candidate against the correct rubric (A/B/C) before human sees it. Cannot pass below 95 for project modes. |
| DNA Store | Persistent database of every approved character's exact visual specification |
| Approval Pipeline | Human-facing conversation layer — text input, candidate presentation, adjustment handling |
| Project Registry | Master project state — palette, proportion system, animation standards, all assets |
| Sheet Manager | Non-destructive sprite sheet management — reads/writes using layout manifests |
| Export Engine | Converts approved assets to target engine formats |
| Web UI | Full local web interface — chat, 1×/4× sprite preview, approve/reject controls, project tabs, freeform tab, continuity manifest viewer. See Section 14. |

---

## 4. The Character DNA System

### 4.1 What DNA Is

Character DNA is the complete, exact, pixel-level specification of an approved character. It is extracted from the approved master sprite the moment a character design is confirmed. It is permanent — changes require a formal re-approval process and regeneration of all derived sprites.

DNA is not a description of what the character looks like. It is a technical blueprint from which any future sprite of this character can be generated exactly — today or three years from now.

### 4.2 DNA Schema

```json
{
  "character_id": "sam_vendor",
  "character_name": "Sam the Market Vendor",
  "approved_date": "YYYY-MM-DD",
  "version": 1,
  "brief": {
    "personality": "Cheerful and rotund, always wiping hands on apron",
    "role": "NPC — market vendor",
    "defining_trait": "Stained apron, gap-toothed smile, bald with fringe"
  },
  "profiles": {
    "world_sprite": {
      "width": 16,
      "height": 24,
      "context": "overworld_exploration",
      "detail_level": "standard"
    },
    "battle_sprite": {
      "width": 48,
      "height": 64,
      "context": "battle",
      "detail_level": "high"
    },
    "chibi_sprite": {
      "width": 8,
      "height": 16,
      "context": "global_map",
      "detail_level": "minimal"
    }
  },
  "palette": {
    "skin_base": "#C8885A",
    "skin_shadow": "#8B5A2B",
    "skin_highlight": "#E8AA7A",
    "outline_face": "#6B3A1A",
    "apron_base": "#E8E8D0",
    "apron_shadow": "#AAAAAA",
    "apron_stain": "#C8A878"
  },
  "construction_rules": {
    "light_source": "top-left",
    "outline_style": "darkened_local_color",
    "outline_weight": 1,
    "shading_method": "hue_shifted_ramp",
    "max_shades_per_region": 3
  },
  "proportion_notes": "Rotund body, short legs, large head. Head ratio 1:2.5 to body.",
  "unique_colors": ["#C8A878"],
  "master_profile": "world_sprite",
  "animation_sets_completed": ["walk_4_directions"],
  "sprite_sheet_path": "assets/characters/sam_vendor/world.png",
  "continuity_group": "npc_market_district",
  "github_asset_path": "assets/characters/sam_vendor/"
}
```

### 4.3 DNA Lock Warning

The moment a character design is approved, the system presents:

> *"This design is now the DNA source for ALL future sprites of this character across all profiles. Every animation, every scale variant, every future addition will be generated from this DNA. This cannot be changed without re-approving the base design and regenerating all derived sprites. Confirm lock?"*

**DNA locking applies to Modes 1 through 6 only.** Mode 7 (Freeform) is explicitly non-DNA. Freeform outputs do not update the continuity manifest, the DNA store, or any project file. They are standalone PNG exports only.

### 4.4 DNA Extraction Process

After lock confirmation:
1. Sample every unique color, map to body region
2. Record exact pixel dimensions per profile
3. Document outline pixel colors per region
4. Confirm light source direction from shadow placement
5. Identify character-unique colors vs master palette colors
6. Write `CHARACTER_DNA/[character_id].json`
7. Update `CONTINUITY_MANIFEST.md`
8. Regenerate project comparison sheet
9. Git commit: `"DNA locked: [character_name] v1"`

---

## 5. Generation Modes

### 5.1 Mode 1 — Character Creation

**Flow:**

1. Human describes character in natural language
2. System asks: *"What sprite profiles do you need?"* — human responds naturally
3. System proposes profile set with dimensions, awaits confirmation
4. **System asks: "Is this a large or multi-tile enemy/boss?"** — if yes, activates large-format mode (see below)
5. System generates master profile (highest detail) — single forward-facing sprite
6. Approval loop: present candidate at 1x and 4x zoom → human adjusts or confirms
7. On confirmation: DNA Lock Warning → extract DNA → generate full master profile sheet
8. System works down through derived profiles (lower detail, same DNA)
9. Each derived profile: generate candidate → confirm reads correctly at scale → generate sheet
10. Final git commit with all sheets and DNA

**Rules:**
- Every candidate scored against rubric before human sees it
- Human never sees a sub-95 sprite unless 5 attempts all fail (system reports scores and failure reasons)
- Adjustment requests applied as targeted deltas, not full regeneration
- Every sheet frame individually evaluated against rubric AND DNA continuity

**Portrait Profile:**
Portrait art is a standard profile type available to any character. Portraits are larger canvas (typically 48x48 to 64x64), higher detail, more expressive than battle sprites. When a portrait profile is requested, the system generates a forward-facing bust portrait first, runs approval loop, then generates any expression variants (neutral, happy, sad, angry, surprised) using the approved portrait as the DNA source. Portrait palette is derived from character DNA but may use additional detail colors (max 4 unique) to support the higher resolution.

**Large-Format / Multi-Tile Boss Mode:**
Standard battle sprites max at 64x64. Large bosses — those spanning multiple tile slots — require a multi-tile composition system. When large-format flag is set:
- Human specifies approximate total dimensions (e.g., 96x96, 128x64, 96x128)
- System designs the boss as a unified composition, then segments it into legal SNES tile-sized pieces
- Each tile segment is generated and evaluated individually for technical compliance
- Composition is also evaluated as a whole for visual coherence and readability
- The sheet manifest tracks tile grid layout so the engine can reassemble the boss correctly
- Animation frames for multi-tile bosses animate all tile segments in sync

### 5.2 Mode 2 — Sprite Sheet Extension

**Use case:** Adding animations to existing characters — today or years later.

**Flow:**
1. Human requests additional sprites: *"Sam needs a surprised reaction — arms up, eyes wide, 2 frames"*
2. System loads `CHARACTER_DNA/sam_vendor.json` — does NOT re-derive from sheet image
3. System loads `SHEET_LAYOUT/sam_vendor_world.json` — identifies empty rows
4. Generates new frames using DNA as sole reference
5. Places in empty rows only — never modifies existing sprite pixels
6. Updates sheet layout manifest
7. Git commit: `"Sam vendor: added surprise animation (2 frames)"`

**Non-destructive guarantee:**
The system maintains a `SHEET_LAYOUT` manifest per sheet. Occupied cells are locked. New sprites only go into empty cells. If no empty cells exist, sheet is expanded and manifest updated.

### 5.3 Mode 3 — Environment, Tileset & Parallax Generation

**The Aesthetic Proof:**
Before generating a full tileset, the system produces a composed sample scene (~10x8 tiles) showing a representative subset of tiles — enough to evaluate the visual vibe, color temperature, and style coherence. This is not a technical preview of individual tiles. It is a holistic feel sample.

**Tileset Flow:**
1. Human describes environment in natural language
2. System generates tile inventory list — all tile types needed including transition tiles
3. System generates Aesthetic Proof scene using representative subset
4. Approval loop: adjust vibe until confirmed
5. On confirmation: system locks a **Tileset Anchor** — the approved set of seed tiles whose palette, texture language, and detail density all subsequent tiles must match
6. Full tileset generated — each tile evaluated against tileset rubric AND seam integrity check AND Tileset Anchor
7. System asks: *"Are there animated tile variants needed?"* (water, torches, foliage, trees swaying, etc.)
8. System asks: *"Are there interactive state variants needed?"* (doors, chests, destructibles, switches)
9. All variants generated as matched sets — same palette, guaranteed seam continuity
10. System checks palette harmony against characters assigned to this environment
11. System asks: *"Are there world map location markers needed for this area?"* (town icon, dungeon icon, castle icon, port icon, etc.) — generates as matched icon set if yes
12. Final organized tileset sheet presented, labeled by category
13. Git commit with full tileset, manifests, and Tileset Anchor record

**Seam Validation:**
Every tile in the set is tested with `seam_validator.py` before approval. All four edges (top, bottom, left, right) must tile seamlessly with their neighbors. Any tile failing seam validation is rebuilt, not patched.

**Transition Tiles:**
Every tileset must include transition tiles — the connecting tiles between different surface types (grass-to-dirt, stone-to-water, road-to-grass). These are explicitly in the tile inventory and evaluated as part of the set, not as an afterthought.

---

### 5.3b Mode 3 Extension — Parallax Battle Backgrounds

Parallax battle backgrounds are architecturally distinct from tilesets and require separate treatment. They are not tilesets. They are multi-layered atmospheric compositions where each layer scrolls at a different speed. Each layer must tile seamlessly horizontally.

**Parallax Flow:**
1. Human provides atmospheric brief: *"The floating continent — ancient ruins suspended in sky, late afternoon light, ominous"*
2. System defines layer stack — typically 3-4 layers:
   - **Sky layer:** farthest back, slowest scroll, sky/atmosphere
   - **Far background:** mountains, distant structures, horizon elements
   - **Midground:** main environmental elements, architecture
   - **Foreground:** closest layer, fastest scroll, decorative framing elements
3. System generates a **Parallax Anchor** — locked palette and atmospheric style before any layer generation begins
4. Each layer is generated as a horizontally-tiling strip at SNES-legal dimensions
5. Each layer evaluated individually: seam integrity, atmospheric consistency with Anchor
6. Composition evaluated with `layer_compositor.py` — assembles all layers at multiple scroll offset ratios to verify depth separation and visual coherence at actual playback
7. Approval loop: human evaluates the composed animation, requests adjustments
8. On confirmation: all layers committed as matched set with composition manifest
9. System verifies character contrast — player/enemy sprites must read clearly against the background

**Parallax evaluation uses the Parallax Background Rubric (see Section 8).** The character rubric does not apply here.

### 5.4 Mode 4 — UI Generation

**Flow:**
1. System presents curated UI style options based on declared game context
2. Human selects preferred style
3. System asks: *"Use as-is or use as a base for customization?"*
4. If customization: natural language adjustment loop
5. On confirmation: generates full UI asset set for that style
6. Assets organized into HUD, menus, dialogue frame, inventory, etc.

**UI asset set includes:**
- Dialogue box frame and variants (standard, wide, tall)
- Menu window frames and cursor
- HUD elements (HP bar, MP bar, status indicators)
- Status condition icons — poison, sleep, silence, blind, stone, berserk, haste, slow, and all other game-specific conditions — generated as a visually coherent icon set
- Element icons — fire, ice, lightning, wind, earth, water, holy, dark — generated as a matched set
- Battle menu layout elements

**Item and Equipment Icons (absorbed into Mode 4):**
Item icons are 16x16 sprites with their own visual grammar. The system generates these as categorized icon families:
- Weapons (swords, spears, bows, staves, rods) — shared visual language within category
- Armor and accessories
- Consumables (potions, ethers, tents, phoenix downs)
- Key items — unique per item, more illustrative than icon-grammar items
All icons evaluated for category coherence as a set, not just individually. Palette must harmonize with the UI style they live inside.

**World Map Location Markers:**
When a world map tileset is generated, system asks if location markers are needed. Marker types: town, large city, dungeon, castle, port, cave, forest shrine, airship/vehicle. Generated as a matched icon set with consistent size, outline weight, and visual register.

**Title Screen:**
Title screen is a special UI mode accessed explicitly. Human provides: game title text, overall aesthetic direction, key visual elements. System generates:
- Background composition (treated as a single large parallax-style composition)
- Logo/title treatment in the project font style
- Menu prompt elements
Approval loop runs on the overall composition before any element is finalized.

### 5.5 Mode 5 — Font Generation

Treated identically to UI generation — curated options presented, selection made, adjustments applied, full character set generated on confirmation.

---

### 5.6 Mode 6 — Battle Effect Animations

Battle effects are animated sprite sequences used in combat — spell animations, hit impacts, status inflictions, healing glows, summon sequences, death particles. They are completely absent from standard character and tileset pipelines and require their own mode.

**Why a separate mode:**
- Often use non-standard palettes — magical fire uses colors that exist in no character's DNA
- Primary quality criteria are timing and frame economy, not outline technique
- Canvas sizes vary by targeting type (single character vs full screen vs area)
- Frame counts range from 4 (hit flash) to 20+ (summon sequence)

**Effect Taxonomy:**
Every effect belongs to one of these categories, each with defined conventions:
- **Projectile effects** — travel animations for arrows, fireballs, ice shards, wind blades
- **Area explosion effects** — impact blooms for area spells (Meteor, Ultima)
- **Status infliction effects** — visual indicator for poison cloud, sleep sparkles, silence bell
- **Healing effects** — cure glow, regen shimmer, raise light beam
- **Elemental strike effects** — fire burst on hit, ice crystal shatter, lightning fork impact
- **Summon sequences** — longer multi-phase animations for espers/summons (cinematic quality)
- **Hit impact frames** — generic physical hit flash, critical hit burst, miss indicator
- **Death sequences** — enemy defeat animation (dissolve, explode, collapse)
- **Environmental hazard animations** — lava drip, poison swamp bubble, trap trigger

**Flow:**
1. Human describes the effect: *"A fire spell — starts as a small spark at the target, blooms into a full fireball burst across 3 frames, then dissipates in 2 frames"*
2. System identifies effect category and proposes: frame count, canvas size, palette (may use effect-specific palette outside MASTER_PALETTE), targeting type
3. Human confirms or adjusts spec
4. System generates all frames as a sequence
5. Evaluation uses the **Effect Animation Rubric** (see Section 8) — timing and weight are primary criteria
6. Approval loop: human evaluates at actual playback speed
7. On confirmation: frames committed as numbered sequence with effect manifest
8. Effect manifest records: category, frame count, canvas size, palette, targeting type, recommended frame timing in ticks

---

### 5.7 Mode 7 — Freeform Generation

Freeform mode is the escape hatch from the entire DNA, style bible, and SNES constraint system. It exists for situations where a user needs a custom pixel art image that has nothing to do with their current project, or that falls outside any defined asset category.

**When to use freeform:**
- Custom images unrelated to any active game project
- Concept art or mood pieces at non-standard resolutions
- Assets for a game with a completely different aesthetic from the project style bible
- Quick one-off generations for testing or inspiration

**What freeform bypasses:**
- DNA conditioning — no character DNA is loaded or referenced
- MASTER_PALETTE.md — full 256-color vocabulary is available
- SNES hardware constraints — any resolution is valid
- Continuity manifest — freeform outputs are never logged as project assets
- Strict evaluation rubric — the 95/100 gate does not apply; a lighter quality check runs to prevent obvious technical failures

**What freeform does NOT bypass:**
- The anti-pattern detector — pillow shading and banding are still flagged and corrected
- The originality check — outputs still cannot be direct copies of reference material

**Flow:**
1. User invokes freeform from the dedicated freeform tab in the web UI
2. User provides: text description + target resolution (e.g., "a cyberpunk robot, 64x64 pixels")
3. System generates candidate with full 256-color palette, no DNA conditioning
4. Candidate presented at 1x and 4x zoom
5. User approves or requests adjustments — same natural language loop as project modes
6. On approval: exported as standalone PNG to `assets/freeform/` — no DNA extracted, no manifest updated, no git commit to project state
7. Freeform outputs are logged in `logs/freeform_log.md` for reference only

**Implementation notes:**
- `pipeline/modes/mode7_freeform.py` handles this mode
- Freeform uses the same underlying transformer but without DNA conditioning tokens
- Resolution is specified by user — system validates it is a reasonable pixel art size (max 256x256 recommended; larger sizes supported but quality warning issued)
- Freeform outputs cannot be promoted to project assets without going through Mode 1 character creation to extract proper DNA

---

### 6.1 Tab Structure

```
PROJECT: [Game Name]
├── CHARACTERS
│   └── [Character Name]
│       ├── Battle Sprites      (48x64 or larger — detailed animations, multi-tile if boss)
│       ├── Portrait Art        (48x48–64x64 — dialogue portraits, expression variants)
│       ├── World Sprites       (16x24 — walk cycles, interactions)
│       └── Overworld Sprites   (8x16 — chibi global map version)
├── ENEMIES
│   └── [same profile structure — large-format flag for bosses]
├── BATTLE EFFECTS
│   ├── Projectile Effects
│   ├── Area Effects
│   ├── Status Effects
│   ├── Healing Effects
│   ├── Elemental Strikes
│   ├── Summon Sequences
│   ├── Hit Impacts
│   └── Death Sequences
├── TILESETS
│   ├── Towns
│   ├── Dungeons
│   ├── Castles
│   ├── Caves
│   ├── Wilderness
│   └── World Map
│       └── Location Markers    (town, dungeon, castle, port, cave, airship icons)
├── PARALLAX BACKGROUNDS
│   └── [scene name]
│       ├── Sky Layer
│       ├── Far Background
│       ├── Midground
│       └── Foreground
├── UI
│   ├── HUD
│   ├── Menus
│   ├── Dialogue
│   ├── Inventory
│   ├── Item Icons
│   ├── Status Icons
│   ├── Element Icons
│   └── Title Screen
└── FONTS
    └── [font sets by use case]
```

### 6.2 GitHub Integration

- Every project ties to a GitHub repository
- AM Pixel reads the repo on load — scans for existing assets, extracts DNA database automatically
- All approved assets committed to repo on confirmation
- DNA files, sheet manifests, and project registry committed alongside assets
- Users can load existing projects by pointing to their repo
- DNA from existing sprites is extracted on first scan — no redesign required

### 6.3 Multi-Project DNA

When starting a new project:
- Option A: Fresh start — empty DNA store, new style bible
- Option B: Import characters from existing project — loads specified DNA files, excludes others
- Option C: Scan repo — extract DNA from existing sprite sheets automatically

---

## 7. Continuity Enforcement

### 7.1 Three Continuity Checks (run on every completed sprite)

**Check 1 — Palette Family Compliance:**
Every color traceable to named ramp in `MASTER_PALETTE.md`. Any unlisted color must be formally designated as character-unique (max 2 per character).

**Check 2 — Group Comparison:**
On every new completion, regenerate comparison sheet of all project characters at 1x. Evaluate as a group. Weakest sprite in group is a problem regardless of individual score.

**Check 3 — Scene Placement:**
Place sprite against representative tileset from the project. Verify readability, palette harmony, stylistic nativity.

### 7.2 Continuity Manifest

`CONTINUITY_MANIFEST.md` tracks per character:
- Character ID and display name
- Assigned palette ramps
- Canonical height per profile
- Unique color designations
- Light source (default: top-left)
- Continuity group (for scene placement testing)
- Current version and DNA file path

---

## 8. The Evaluation Engine

### 8.1 Philosophy

The evaluation engine is the most important component. Weak evaluation produces confident mediocrity. The engine must be harder than the human eye — not easier.

### 8.2 Rules

- Every sprite evaluated before the human ever sees it
- Cannot rationalize a flaw as a stylistic choice
- Cannot compare to its own earlier work — compares only to best work in reference library
- No partial credit for effort or complexity
- Below 95 = full rebuild from silhouette. Not patching.
- Every rejection documents specific, technical failure points
- Every pass documents what succeeded — added to `LESSONS_LEARNED.md`

### 8.3 The Three Rubrics

**Different asset types require different evaluation criteria.** A single rubric cannot evaluate characters, tilesets, and parallax backgrounds with equal accuracy. Three rubrics are defined. The correct rubric is selected automatically based on asset type.

---

#### Rubric A — Character / Enemy / Portrait / Effect Sprites

Applies to: all character profiles, NPC sprites, enemy sprites, portrait art, boss sprites, battle effects.

| Category | Points | What Is Evaluated |
|----------|--------|-------------------|
| Technical Compliance | 25 | SNES palette limits, tile dimensions, no anti-aliasing, color space |
| Construction Quality | 25 | Outline technique, shading method, hue-shifted ramps, no banding, no pillow shading |
| Readability | 20 | Silhouette clarity at 1x, key feature legibility, character distinguishability |
| Animation Quality | 15 | Weight, timing, frame economy, physicality — evaluated at playback speed |
| Originality | 10 | Cannot be identified as remix of a specific reference sprite |
| Soul | 5 | Does the sprite have personality? Memorable after one encounter? |
| **PASSING THRESHOLD** | **95/100** | **Below 95 = full rebuild** |

*For battle effects specifically: Animation Quality weight increases to 25, Construction Quality decreases to 15 — timing and weight are the primary craft criteria for effects.*

---

#### Rubric B — Tilesets

Applies to: all environment tilesets, world map tilesets, animated tile sets, interactive state tile sets.

| Category | Points | What Is Evaluated |
|----------|--------|-------------------|
| Seam Integrity | 30 | Every edge tiles seamlessly with neighbors on all four sides — zero visible seams at any valid combination |
| Visual Recession | 20 | Tiles read as background — they do not compete with character sprites for attention |
| Texture Coherence | 20 | All tiles share the same texture language, palette feel, and detail density as the Tileset Anchor |
| Atmospheric Consistency | 15 | Set has a unified time-of-day, weather, material feel, and light direction |
| Completeness | 10 | Set includes all required tile types including transition tiles between surface types |
| Technical Compliance | 5 | SNES palette constraints, tile dimensions |
| **PASSING THRESHOLD** | **95/100** | **Below 95 = full rebuild** |

---

#### Rubric C — Parallax Battle Backgrounds

Applies to: all parallax background layer sets.

| Category | Points | What Is Evaluated |
|----------|--------|-------------------|
| Layer Seaming | 25 | Each layer tiles horizontally without visible seams at any scroll position |
| Layer Depth Differentiation | 25 | Layers read as clearly near/far — visual separation holds at multiple scroll offset ratios |
| Atmospheric Cohesion | 20 | All layers share palette feel, light direction, and weather — unified scene |
| Character Contrast | 15 | Background recedes sufficiently that player and enemy sprites read clearly in front of it |
| Emotional Tone | 10 | Does the background communicate the correct feeling for its context |
| Technical Compliance | 5 | Layer dimensions, SNES palette constraints |
| **PASSING THRESHOLD** | **95/100** | **Below 95 = full rebuild** |

### 8.4 Pixel-Diff Tooling

The evaluation engine uses visual diff tools — not just abstract scoring:
- `palette_validator.py` — identifies every out-of-palette pixel with coordinates
- `dna_diff.py` — visual overlay showing DNA deviations in a candidate sprite
- `banding_detector.py` — flags horizontal or vertical color bands
- `outline_checker.py` — identifies pure black outlines (must be darkened local color)
- `rubric_scorer.py` — selects correct rubric (A/B/C) by asset type, returns score with per-category breakdown and specific failure descriptions
- `seam_validator.py` — tests all four edges of every tile for seamless tiling at all valid neighbor combinations
- `tileset_anchor_extractor.py` — derives Tileset Anchor palette, texture language, and detail density from approved seed tiles; all subsequent tiles validated against it
- `layer_compositor.py` — assembles parallax layers at multiple scroll offset ratios for composition evaluation and character contrast testing
- `effect_timing_evaluator.py` — evaluates battle effect animation frame timing and weight at actual playback speed
- `icon_grammar_checker.py` — validates that icon sets (items, status, elements) share consistent visual grammar within categories
- `anti_aliasing_detector.py` — flags sub-pixel blending (not allowed in SNES style)

### 8.5 Anti-Pattern Library

During training the system explicitly generates intentionally bad sprites — pillow shaded, banded, wrong proportions, pure black outlines — and contrasts them against correct versions. This sharpens evaluation accuracy by giving the engine direct experience of failure modes in its own output rather than only theoretical descriptions.

---

## 9. The Self-Training Layer

### 9.1 Boot Training Phase (Pre-Production)

No production sprites generated until Boot Training is complete and all gate criteria are met.

**Research directives:**
The system actively searches for — does not use a fixed list — the best available resources across:
- SNES and multi-platform hardware constraint documentation (minimum 6 platforms)
- Reference games (minimum 40 games, minimum 6 platforms, artist-cited not just popular)
- Pixel art theory — prioritize resources that explain WHY not just HOW
- Critique examples — before/after annotated comparisons are highest value training data
- Animation principles — traditional theory adapted to pixel art
- Color theory foundations — Munsell, Albers, Gurney applied to pixel art palette construction
- Cross-cultural study — Western vs Eastern pixel art philosophical differences

**Completion gate — all must be true:**
- Hardware constraints documented for 6+ platforms
- 40+ reference games across 6+ platforms with annotated analysis
- 20+ resources rated 7+ on quality criteria
- 20+ universal principles extracted and evidenced
- 15+ failure modes documented with corrective principles
- Evaluation rubric complete with measurable criteria

### 9.2 Practice Gauntlet (Pre-Production Validation)

After Boot Training, before any production work:
- Generate 10+ complete practice characters across different archetypes
- Full overworld walk cycle for each (4 directions × 3 frames)
- Minimum 3 must fail and require rebuild — failures documented
- Final 5 must show measurable improvement over first 5
- Full group continuity check must pass
- Anti-pattern library must contain 10+ documented failure examples with corrections

### 9.3 Continuous Training Protocol

After every 5 production sprites:
1. Rebuild the weakest sprite in the full project set
2. Extract lessons from the strongest sprite
3. Search for new pixel art resources — integrate if quality threshold met
4. Review and update `MISTAKE_TAXONOMY.md`
5. Approved production assets added to fine-tuning dataset

Root cause analysis triggers if any sprite requires 5+ rebuild cycles.

---

## 10. Style Modes

### 10.1 SNES Style (Default)
Trains for the SNES aesthetic — palette feel, proportion conventions, outline technique, color ramp character. Hardware constraints are not enforced by default but available as a toggle.

### 10.2 Hardware Constraint Toggle
When enabled, adds a post-processing compliance filter:
- Max 15 colors + 1 transparent per sprite palette
- SNES-legal tile dimensions
- 15-bit RGB color space enforcement
- No sub-pixel rendering

Style-first training is the correct direction. Hardware constraints as a filter layer on top is the correct implementation. The reverse — training hardware-constrained — would produce a model fighting its own learned behavior when the toggle is off.

### 10.3 Future Style Expansion
Additional style models unlock after hitting 99/100 production threshold in current style:
- NES style
- Game Boy / GBC style
- 32-bit PS1 era
- Custom style bible (user-defined)

---

## 11. Export Formats

| Engine | Format | Notes |
|--------|--------|-------|
| Godot 4.x | SpriteFrames resource + PNG | Animation metadata included |
| RPG Maker MZ | Sprite sheet PNG with MZ naming conventions | Character, face, tileset formats |
| GameMaker | PNG sprite sheet + JSON animation data | |
| Unity | PNG sprite sheet + animation clip metadata | |
| Generic | PNG sprite sheet + JSON manifest | Universal fallback |

---

## 12. Deployment Architecture

### 12.1 Local Mode (Development)
- Model runs locally on developer machine
- Full generation pipeline on-device
- No usage limits
- Used by Absentmind for development and testing

### 12.2 Server Mode (Production/Commercial)
- Model lives server-side — never distributed to users
- Users interact via client application calling inference API
- API authenticated per user account
- Generation requests logged for quality monitoring and fine-tuning dataset curation

### 12.3 Freemium Tiers
| Tier | Generations | Commercial License | Notes |
|------|-------------|-------------------|-------|
| Free | Limited per month | Personal use only | Enough to evaluate quality |
| Indie | Unlimited | Full commercial | Solo developer subscription |
| Studio | Unlimited + API | Full commercial | Team accounts + API access |

---

## 14. User-Facing Web Interface

AM Pixel is operated through a local web UI served by FastAPI. This is not optional — it is a required deliverable. A solo developer cannot be expected to run Python scripts in a terminal to approve sprites. The web UI is the product's face.

### 14.1 Requirements

**Chat panel:**
Natural language input for all generation requests. Supports all seven modes. Mode is auto-detected from context or selectable via tab. Conversation history maintained per session.

**Sprite preview panel:**
Every generated candidate displayed at both 1x (actual pixel size) and 4x (zoomed) simultaneously. For sprite sheets, individual frame playback at selectable speed. For parallax backgrounds, multi-layer scroll simulation at adjustable speed ratios.

**Approval controls:**
- Approve — locks the candidate, triggers DNA extraction if applicable, proceeds to next step
- Reject — sends back to generation with optional adjustment note
- Adjust — opens text input for natural language adjustment request without full rejection

**Project tabs:**
Mirror the project organization structure defined in Section 6.1. Each tab shows assets in that category as a visual grid. Clicking any asset opens its DNA record, sheet layout, and generation history.

**Freeform tab:**
Dedicated tab for Mode 7. Separate from project tabs. Resolution input field. No DNA or project state shown — clean blank canvas interface.

**Continuity manifest viewer:**
Read-only view of `CONTINUITY_MANIFEST.md` rendered as a visual table. Shows all characters, their palette assignments, continuity groups, and profile completion status.

**Hardware status bar:**
Persistent display of: GPU VRAM usage, current phase, training status, disk usage. Alerts if any resource approaches limits.

### 14.2 Technical Implementation

- **Server:** FastAPI serving both the inference API and the web UI
- **Frontend:** Single-page HTML/JS application — no external framework dependencies required; keep it simple and functional
- **Entry point:** `ui/app.py`
- **Templates:** `ui/templates/` — HTML templates
- **Static assets:** `ui/static/` — CSS and JS
- **Local only:** Web UI serves on localhost only (127.0.0.1) — never exposed to external network in local mode
- **Server mode:** In production deployment, UI is replaced by a proper client application calling the server-side inference API

### 14.3 Build Priority

The web UI skeleton (working chat panel + image preview + approve/reject controls) must be complete and functional before the Practice Gauntlet begins. OpenClaw cannot validate the approval workflow without a working UI to validate it through.

---

## 15. Technical Stack

- **Model:** Custom PyTorch transformer, CUDA training
- **Hardware:** NVIDIA GPU, minimum 10GB VRAM (CUDA required). If local GPU is insufficient for training, use cloud GPU rental (RunPod, Vast.ai, Lambda Labs) for training runs only — inference can run on lower VRAM.
- **Image tooling:** Pillow for pixel-level manipulation and validation
- **Sheet management:** Custom Python tools using layout manifests
- **Project state:** JSON manifests + Markdown human-readable files
- **Version control:** Git — every approval event is a commit
- **API layer:** FastAPI (inference endpoint + web UI server)
- **Web UI:** FastAPI + plain HTML/JS (localhost only in local mode)
- **Training data management:** Custom curation pipeline with quality scoring

---

*AM Pixel Specification v1.1 | Absentmind Studio*
