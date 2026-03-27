# AM Pixel — Full Technical Specification
**Absentmind Studio | Version 1.0**

---

## 1. Product Definition

AM Pixel is a purpose-built AI sprite generator and game asset manager for retro-style pixel art games. It produces original, studio-quality pixel art assets through natural language conversation, with a character DNA system that enforces perfect visual continuity across all assets in a project.

AM Pixel is not a wrapper around Stable Diffusion, Midjourney, or any existing image generation model. It is a custom-built autoregressive transformer that generates sprites natively in palette-index space — the same way a language model generates tokens. This architecture is the core innovation that makes pixel-perfect DNA enforcement possible.

---

## 2. Quality Standard

The quality target is work that a pixel art expert cannot reliably distinguish from professional SNES-era studio output. This is not aspirational — it is the shipping standard. Assets that do not meet this bar are not presented to the user.

**Passing threshold: 95/100 on the AM Pixel evaluation rubric.**
**Production threshold: 99/100 of generations pass without rebuild.**

Until the 99/100 production threshold is met, the model is not in production. It is still training.

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
| Evaluation Engine | Scores every candidate against rubric before human sees it. Cannot pass below 95. |
| DNA Store | Persistent database of every approved character's exact visual specification |
| Approval Pipeline | Human-facing conversation layer — text input, candidate presentation, adjustment handling |
| Project Registry | Master project state — palette, proportion system, animation standards, all assets |
| Sheet Manager | Non-destructive sprite sheet management — reads/writes using layout manifests |
| Export Engine | Converts approved assets to target engine formats |

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
4. System generates master profile (highest detail) — single forward-facing sprite
5. Approval loop: present candidate at 1x and 4x zoom → human adjusts or confirms
6. On confirmation: DNA Lock Warning → extract DNA → generate full master profile sheet
7. System works down through derived profiles (lower detail, same DNA)
8. Each derived profile: generate candidate → confirm reads correctly at scale → generate sheet
9. Final git commit with all sheets and DNA

**Rules:**
- Every candidate scored against rubric before human sees it
- Human never sees a sub-95 sprite unless 5 attempts all fail (system reports scores and failure reasons)
- Adjustment requests applied as targeted deltas, not full regeneration
- Every sheet frame individually evaluated against rubric AND DNA continuity

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

### 5.3 Mode 3 — Environment & Tileset Generation

**The Aesthetic Proof:**
Before generating a full tileset, the system produces a composed sample scene (~10x8 tiles) showing a representative subset of tiles — enough to evaluate the visual vibe, color temperature, and style coherence. This is not a technical preview of individual tiles. It is a holistic feel sample.

**Flow:**
1. Human describes environment in natural language
2. System generates tile inventory list — all tile types needed
3. System generates Aesthetic Proof scene
4. Approval loop: adjust vibe until confirmed
5. Full tileset generated — each tile evaluated against rubric AND internal tileset consistency
6. System asks: *"Are there animated tile variants needed?"* (water, torches, foliage, etc.)
7. System asks: *"Are there interactive state variants needed?"* (doors, chests, destructibles)
8. All variants generated as matched sets — same palette, guaranteed consistency
9. System checks palette harmony against characters assigned to this environment
10. Final organized tileset sheet presented, labeled by category
11. Git commit with full tileset and manifests

### 5.4 Mode 4 — UI Generation

**Flow:**
1. System presents curated UI style options based on declared game context
2. Human selects preferred style
3. System asks: *"Use as-is or use as a base for customization?"*
4. If customization: natural language adjustment loop
5. On confirmation: generates full UI asset set for that style
6. Assets organized into HUD, menus, dialogue frame, inventory, etc.

### 5.5 Mode 5 — Font Generation

Treated identically to UI generation — curated options presented, selection made, adjustments applied, full character set generated on confirmation.

---

## 6. Project Organization

### 6.1 Tab Structure

```
PROJECT: [Game Name]
├── CHARACTERS
│   └── [Character Name]
│       ├── Battle Sprites      (48x64 or similar — detailed animations)
│       ├── World Sprites       (16x24 — walk cycles, interactions)
│       └── Overworld Sprites   (8x16 — chibi global map version)
├── ENEMIES
│   └── [same profile structure as characters]
├── TILESETS
│   ├── Towns
│   ├── Dungeons
│   ├── Castles
│   ├── Caves
│   ├── Wilderness
│   └── World Map
├── PARALLAX
│   └── [scene-specific layered backgrounds]
├── UI
│   ├── HUD
│   ├── Menus
│   ├── Dialogue
│   └── Inventory
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

### 8.3 Rubric Categories

| Category | Points | What Is Evaluated |
|----------|--------|-------------------|
| Technical Compliance | 25 | SNES hardware accuracy, palette limits, tile dimensions, no anti-aliasing |
| Construction Quality | 25 | Outline technique, shading method, color ramp quality, no banding, no pillow shading |
| Readability | 20 | Silhouette clarity at 1x, key feature legibility, character distinguishability |
| Animation Quality | 15 | Weight, timing, frame economy, physicality — evaluated at playback speed |
| Originality | 10 | Cannot be identified as remix of a specific reference sprite |
| Soul | 5 | Does the sprite have personality? Memorable after one encounter? |
| **PASSING THRESHOLD** | **95/100** | **Below 95 = full rebuild** |

### 8.4 Pixel-Diff Tooling

The evaluation engine uses visual diff tools — not just abstract scoring:
- `palette_validator.py` — identifies every out-of-palette pixel with coordinates
- `dna_diff.py` — visual overlay showing DNA deviations in a candidate sprite
- `banding_detector.py` — flags horizontal or vertical color bands
- `outline_checker.py` — identifies pure black outlines (must be darkened local color)
- `rubric_scorer.py` — returns numeric score with per-category breakdown and specific failure descriptions

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

## 13. Technical Stack

- **Model:** Custom PyTorch transformer, CUDA training
- **Hardware:** NVIDIA GPU, minimum 10GB VRAM (CUDA required)
- **Image tooling:** Pillow for pixel-level manipulation and validation
- **Sheet management:** Custom Python tools using layout manifests
- **Project state:** JSON manifests + Markdown human-readable files
- **Version control:** Git — every approval event is a commit
- **API layer:** FastAPI (server inference endpoint)
- **Client:** TBD (Electron desktop app or web client)
- **Training data management:** Custom curation pipeline with quality scoring

---

*AM Pixel Specification v1.0 | Absentmind Studio*
