# AM Pixel — Full Technical Specification
**Absentmind Studio | Version 1.5**

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
- Hardware target: Universal — detected automatically at startup. See Section 14 Technical Stack for detection hierarchy.
- **Positional encoding: 2D, not 1D.** Each token receives two independent learned embeddings — one for canvas X coordinate, one for canvas Y coordinate — summed at the input layer. Standard 1D sequence positional encoding is not used as the primary spatial signal. Because structure-aware token ordering scrambles spatial sequence position, 1D encodings would encode sequence distance rather than canvas proximity. 2D canvas coordinate embeddings give every token its true spatial position regardless of generation order. See CHANGE-010.

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

**Structure-aware token ordering (CHANGE-001):**
Training sequences are NOT stored in raster order (left-to-right, top-to-bottom). They are reordered into structure-aware order that mirrors how a professional pixel artist actually constructs a sprite:

1. **Transparent pixels first** — the full alpha mask, committing to the spatial boundary before any visible content
2. **Outline pixels second** — the single-pixel silhouette border
3. **Base fill pixels third** — large flat color regions (body, clothing, skin)
4. **Shading pixels fourth** — shadow and highlight ramps applied to base fills
5. **Detail pixels last** — small features, accessories, face details

Positional encodings preserve the original (x, y) canvas coordinates so the model can reconstruct spatial position regardless of generation order. See §3.1 for the 2D positional encoding implementation. The transformer architecture itself is unchanged — only the ordering of training sequences changes. At inference time, the model generates in the same learned order.

**Pixel classification — four categories for foundation training (CHANGE-014):**
For Stage 1 foundation training, the pixel classifier uses four categories rather than five. The shade/detail boundary is semantically ambiguous in scraped sprite data without understanding the artistic context — a highlight on shiny armor could be classified as either. Inconsistent classification produces inconsistent token ordering, which produces inconsistent training signal. The four-category version is reliable from pixel geometry alone:

1. **Transparent** — alpha = 0
2. **Outline** — non-transparent pixels adjacent to transparent pixels
3. **Structural** — large contiguous regions of a single palette index
4. **Non-structural** — everything else (captures shade and detail combined)

For Stage 2 quality fine-tuning, the full five-category classification may be applied to the curated Golden Dataset where data quality is controlled and output can be human-verified. The `--full-five-category` flag in `pixel_classifier.py` enables this; it is disabled by default.

**Phase 4 experiment requirement:** Compare structure-aware ordering vs raster ordering on a held-out validation set during Phase 4. If structure-aware ordering does not produce measurable improvement in rubric scores, revert to raster. Document the comparison in `logs/training_log.md`.

The data pipeline must log the distribution of all four pixel categories across the training corpus. If any category is severely underrepresented, this will cause generation failures and must be caught during Phase 3 before training begins.

**Two-tier corpus strategy (CHANGE-019):**
The training corpus is divided into two tiers with different quality standards and different roles in the training pipeline.

**Tier 1 — Golden Dataset (primary quality signal):**
A manually curated set of 3,000–5,000 sprites, individually verified to be correctly extracted, SNES-aesthetic compliant, correctly palette-indexed, and free of pillow shading and banding. Every sprite in this set has been human-reviewed. This is the most important work in Phase 3. It is not a cleanup pass after scraping — it is the primary Phase 3 deliverable. Building it is slow and cannot be rushed. Commissioned sprites and community-contributed CC0 sprites (see CHANGE-024) are preferred sources over scraped sprites for this tier. Golden Dataset sprites are stored in `data/golden/`.

**Tier 2 — Broad Corpus (volume and variety):**
Algorithmically scraped and filtered sprites, target 30,000–50,000. Quality is lower and inconsistent. Used for Stage 1 foundation training to give the model exposure to variety. Stored in `data/corpus/train/` and `data/corpus/validation/`.

Training strategy: pre-train on Tier 2 (broad exposure), fine-tune on Tier 1 (quality signal). Stage 1 = Tier 2 corpus. Stage 2 = Tier 1 corpus.

**Paired-view training sequences (CHANGE-017):**
Many sprite sheets contain the same character from multiple directions — standard for RPG walk cycles. The data pipeline must actively identify and preserve these view pairs rather than treating each direction as an independent sprite. Confirmed pairs are stored with a `view_pair_id` linking them and are used in a higher-weight training sequence format:

`[DNA] + [Brief] + [View A Tokens]` → `[View B Tokens]`

This teaches the model view rotation geometry implicitly — that a nose disappears as the face rotates, that shoulder width contracts in side view, that occluded features emerge when the angle changes. Target: minimum 20% of training examples should be paired-view sequences. Synthetic pairs (simple reflections) may supplement confirmed pairs but are labeled separately with lower training weight.

**Training data provenance (CHANGE-023):**
Every sprite entering the training pipeline must have a corresponding entry in `data/TRAINING_PROVENANCE_MANIFEST.json` before it is used for training. This manifest is the legal record of what the model was trained on. It is never deleted. See §15 Training Data Provenance and CHANGE-023 for the full legal rationale.

### 3.3 System Components

| Component | Responsibility |
|-----------|----------------|
| Training Engine | Self-directed research, corpus curation, model training, quality fine-tuning |
| Generation Engine | Custom transformer inference — produces sprite candidates from DNA + prompt |
| Freeform Engine | Unconstrained generation mode — bypasses DNA and style bible, uses full 256-color vocabulary, any resolution, outputs PNG only. See Mode 7. |
| Compliance Layer | `tools/compliance.py` — emergency halt, DNA lock gate, phase advance gate, training run gate, provenance gate. Irreversible pipeline actions require gate checks (CHANGE-028). |
| Evaluation Engine | Scores every candidate against the correct rubric (A/B/C) before human sees it. Cannot pass below 95 combined for project modes. Automated gate 85/85 first. |
| DNA Store | Persistent database of every approved character's exact visual specification |
| Approval Pipeline | Human-facing conversation layer — text input, candidate presentation, adjustment handling, optional prompt expansion for character briefs |
| Project Registry | Master project state — palette, proportion system, animation standards, all assets |
| Sheet Manager | Non-destructive sprite sheet management — reads/writes using layout manifests |
| Export Engine | Converts approved assets to target engine formats |
| Web UI | Full local web interface — chat, 1×/4× sprite preview, approve/reject controls, project tabs, freeform tab, continuity manifest viewer. See Section 13. |

---

### 3.4 Known Architectural Risks — Decisions Required Before Phase 4

These are documented risks in the autoregressive architecture that must be explicitly addressed before the transformer is built. They cannot be retrofitted cleanly after Phase 4 begins.

---

**Risk A — Sequence Length and Error Accumulation (CHANGE-007)**

Autoregressive models accumulate prediction errors over long sequences. A 16×24 world sprite is 384 tokens — manageable. A 48×64 battle sprite is 3,072 tokens. At that length, errors from early tokens compound and the bottom/right portion of the sprite degrades into anatomical inconsistency or palette drift. This is a documented failure mode in every pixel-level autoregressive model from PixelCNN onward. The 99/100 batch threshold will be very difficult to hit consistently at battle-sprite scale without explicit mitigation.

Structure-aware generation order (CHANGE-001) partially mitigates this by front-loading structurally critical tokens. It is not a complete fix for sequences above ~1,500 tokens.

**Phase 4 gate — sequence length evaluation:**
After initial training, generate 50 sprites across a range of sizes. Measure pass rate separately for sequences under 1,500 tokens vs over 1,500 tokens. If pass rate for sequences over 1,500 tokens falls below 70%, implement hierarchical generation before proceeding to Phase 5.

**Hierarchical generation (if needed):**
Generate a coarse low-resolution palette grid first (e.g., 6×8 for a 48×64 sprite at 8× downscale), then autoregressively refine at progressively higher resolutions, conditioning each scale on the previous output plus the DNA. This slashes effective sequence length per step and gives the model global structure before committing to fine detail. More architecturally complex but has the strongest theoretical basis for long-sequence coherence.

---

**Risk B — DNA Conditioning Signal Dilution at Long Sequences (CHANGE-008)**

The current spec conditions generation by prepending DNA JSON as context tokens. For 16×24 sprites (384 tokens) this works well. For 48×64 battle sprites (3,072 tokens), the attention mechanism must span thousands of tokens back to the DNA prefix. In practice, the conditioning signal weakens — later tokens are less tightly constrained by the DNA than earlier ones. This means a battle sprite's lower body may be less palette-accurate than its head and shoulders.

**Implementation — Start with prefix conditioning (current spec):**
Build exactly as specified — DNA JSON prepended as context tokens. Measure conditioning strength empirically.

**Phase 4 measurement task:**
After initial training, generate 20 battle sprites. Run `dna_diff.py` separately on the top half vs. bottom half of each sprite. Document the delta in DNA consistency score. If bottom-half consistency is more than 10% lower than top-half consistency consistently, upgrade to cross-attention conditioning in Phase 6.

**Cross-attention upgrade path (if needed):**
The DNA JSON is encoded into a fixed set of learned conditioning vectors that attend to every token prediction step via dedicated cross-attention layers. The DNA signal is equally strong at token 1 and token 3,072. Architecturally more complex — requires adding cross-attention heads — but eliminates conditioning dilution entirely.

Do not build cross-attention from the start without evidence it is needed. Test the simple version first.

---

**Risk C — Animation Temporal Coherence (CHANGE-009)**

The current spec generates each animation frame independently, conditioned only on the shared DNA. This enforces character continuity (same colors, same proportions) but not motion continuity. A walk cycle generated frame-by-frame will have consistent character identity but may not read as a coherent motion sequence — frames may look like the same character drawn multiple times rather than the same character in motion.

**Phase 7-8 evaluation task:**
After the full pipeline is integrated, evaluate whether frame-independent generation with DNA conditioning is sufficient for walk cycles at the 95/100 rubric threshold. Specifically: does the walk cycle fail the Animation Quality rubric category for motion reasons rather than character reasons?

**Temporal conditioning upgrade path (if needed):**
Condition each frame on the previous frame's token sequence plus the shared DNA. This stays fully within the discrete palette-index token architecture. Only implement if frame-independent generation demonstrably fails motion quality rubric criteria.

Do not build temporal conditioning speculatively.

**Skeletal pose tokens — secondary upgrade path (CHANGE-015):**
If raw-token temporal conditioning produces stiff or copy-prone animation (the model copies rather than transforms), the next step is skeletal pose token conditioning. A lightweight rule-based script extracts a simplified 2D skeleton from each frame — center of mass of head, torso, and approximate limb endpoints (~10–12 key points for a battle sprite). Frame 2 is then conditioned on DNA + Brief + Frame 1 skeleton tokens (not raw pixel tokens). Skeleton tokens are ~10–12 tokens vs 384–3,072 raw pixel tokens, dramatically reducing context length and giving the model an explicit motion representation rather than forcing it to infer motion from pixel deltas. A stub `data/pipeline/pose_extractor.py` is initialized in Phase 0. Only implement if raw-token conditioning demonstrably fails.

---

**Risk D — 2D Positional Encoding Implementation (CHANGE-010)**

Structure-aware token ordering scrambles the spatial sequence position of tokens. Standard 1D positional encodings (sinusoidal or RoPE) encode position in the token sequence, not position on the canvas. A token at sequence position 1 (transparent, canvas 0,0) and a token at sequence position 847 (outline, canvas 15,5) may be spatially adjacent but will appear far apart to a 1D positional encoder — forcing the model to learn spatial relationships indirectly from sequence distance. This degrades spatial coherence, potentially undermining the benefit of structure-aware ordering entirely.

**Implementation requirement:**
Use 2D positional encodings as specified in §3.1. Each token's embedding is the sum of three components: palette index embedding + learned X coordinate embedding + learned Y coordinate embedding. The embedding lookup tables for X and Y coordinates are trained, not fixed sinusoidal. DNA conditioning tokens do not carry canvas coordinates — they use a separate learned embedding type to distinguish them from sprite tokens.

`data/pipeline/sequence_reorderer.py` must output `(palette_index, canvas_x, canvas_y)` tuples, not bare palette indices. The transformer input layer consumes all three values per token.

This is not optional. Building the transformer with 1D positional encodings and structure-aware ordering is an architectural contradiction that will produce worse results than raster ordering with 1D encodings.

---

**Note on MaskGIT (CHANGE-011):**
Masked Generative Transformers (MaskGIT) have been raised by multiple reviewers as an alternative to autoregressive generation — primarily for inference speed. This project does not optimize for speed. Accuracy is the priority. MaskGIT is documented in PROPOSED_CHANGES_002 as a Phase 4 optional experiment: if batch generation time becomes a demonstrated practical blocker (not a theoretical concern), evaluate MaskGIT at that point. Do not switch architectures speculatively. See README.md — On Speed vs. Accuracy.

### 4.1 What DNA Is

Character DNA is the complete, exact, pixel-level specification of an approved character. It is extracted from the approved master sprite the moment a character design is confirmed. It is permanent — changes require a formal re-approval process and regeneration of all derived sprites.

DNA is not a description of what the character looks like. It is a technical blueprint from which any future sprite of this character can be generated exactly — today or three years from now.

**DNA encodes what is visible. The Brief encodes what exists.**
DNA extraction is pixel-based — it can only record features present in the master sprite. Any feature occluded in the master view (a backpack hidden behind the body, a ponytail hidden under a hood, a rear armor plate, a tail) will not appear in the DNA. These features must be recorded in the `brief.occluded_features` field and will be used as conditioning input when generating non-master views. See §4.3 and §5.1 for how this affects multi-view generation.

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
    "defining_trait": "Stained apron, gap-toothed smile, bald with fringe",
    "occluded_features": []
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

**`occluded_features` field:** An array of plain-language descriptions of every feature that exists on this character but is not visible in the master sprite. This field is the only record of hidden features and is required conditioning input for all non-master view generation. Examples: `"Large iron-frame backpack with bedroll strapped to top"`, `"Long brown ponytail reaching mid-back, tied with red cord"`, `"Rear pauldron with clan sigil on right shoulder blade"`. An empty array is valid for characters with no hidden features.

### 4.3 DNA Lock Warning

The moment a character design is approved, the system presents:

> *"Before locking DNA, confirm that your character brief is complete. The brief must describe ALL features of this character — including features not visible in the current sprite (backpacks, tails, ponytails, rear armor, hidden accessories). The `occluded_features` field is the only record of hidden features. Once DNA is locked, multi-view generation will use the brief to render these features. If the brief is incomplete, those features will not appear in side or rear views.*
>
> *This design is now the DNA source for ALL future sprites of this character across all profiles. Every animation, every scale variant, every future addition will be generated from this DNA. This cannot be changed without re-approving the base design and regenerating all derived sprites. Confirm lock?"*

> **⚠️ ROLLBACK COST WARNING (CHANGE-029):** A full DNA rollback on a character with complete animation sets requires regenerating 40+ frames across all profiles, each through the full approval loop. A rollback can represent as much work as the original character creation. Confirm the brief is complete and the design is correct before locking.

**DNA locking applies to Modes 1 through 6 only.** Mode 7 (Freeform) is explicitly non-DNA. Freeform outputs do not update the continuity manifest, the DNA store, or any project file. They are standalone PNG exports only.

### DNA Rollback Procedure (CHANGE-029)

Locked DNA is intended to be permanent. When locked DNA must be revised, follow this procedure — **OpenClaw does not initiate a rollback without explicit human authorization (Step 1).**

1. **Human approval:** The human confirms rollback is authorized and states the reason in writing. Document in `logs/rebuild_log.md` and `logs/decision_log.md`. No rollback work begins before this.
2. **Identify scope:** Locate the `"DNA locked: [character_name] v1"` git commit. All sprites committed after that reference this DNA as derived. Sheet manifests record which DNA version each frame used.
3. **Invalidate derived sprites:** Mark derived frames as `"status": "superseded_by_rollback_v2"` in sheet manifests. Do not delete PNGs — git preserves history; manifests flag them as non-authoritative.
4. **Revised master candidate:** Generate a new master under the revision brief; full Mode 1 approval loop. Human must approve the new master before any v2 DNA exists. Only after approval does `dna_extractor.py` produce `[character_id]_v2.json`.
5. **Commit v2 DNA:** Git message: `"DNA revised: [character_name] v1 → v2 — [reason]"`. Retain `_v1.json` permanently. Update `CONTINUITY_MANIFEST.md`: v1 marked `"status": "superseded", "superseded_by": "v2"`; v2 active.
6. **Regenerate derived profiles:** Rebuild all derived profiles from v2 DNA; each through approval. Commit per profile: `"DNA rollback regeneration: [character_name] [profile] v2"`.

### 4.4 DNA Extraction Process

After lock confirmation:
1. Sample every unique color, map to body region
2. Record exact pixel dimensions per profile
3. Document outline pixel colors per region
4. Confirm light source direction from shadow placement
5. Identify character-unique colors vs master palette colors
6. Display extraction summary and prompt: *"Are there any features of this character not visible in this sprite? Add them to occluded_features before locking."*
7. Write `dna/characters/[character_id]_v1.json` — version tracks **approved master design count**, not attempt count (CHANGE-029). First lock is always `_v1`.
8. Update `CONTINUITY_MANIFEST.md`
9. Regenerate project comparison sheet
10. Git commit: `"DNA locked: [character_name] v1"`

**Versioned files:** DNA JSON filenames use `[character_id]_vN.json` (e.g. `sam_vendor_v1.json`, `sam_vendor_v2.json` after a formal rollback). Older versions stay in git; never delete prior JSON versions.

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
8. System works down through derived profiles (lower detail, same DNA) — **each non-master profile is generated using twin input: `[DNA] + [Complete Brief including occluded_features] + [Master View Tokens]`. Not DNA alone.** The master view tokens provide visual grounding; the complete brief ensures occluded features (backpacks, ponytails, rear armor) appear in side and rear views where they would be visible.
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
2. System loads `dna/characters/sam_vendor.json` — does NOT re-derive from sheet image
3. System loads `sheets/sam_vendor_world.json` — identifies empty rows
4. Generates new frames using DNA as sole reference
5. Places in empty rows only — never modifies existing sprite pixels
6. Updates sheet layout manifest
7. Git commit: `"Sam vendor: added surprise animation (2 frames)"`

**Non-destructive guarantee:**
The system maintains a `sheets/` manifest per sheet. Occupied cells are locked. New sprites only go into empty cells. If no empty cells exist, sheet is expanded and manifest updated.

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

**Sliding Window Boundary Conditioning (CHANGE-012):**
Tiles are not generated in isolation. When generating tile at canvas position (x, y), the following are prepended as hard conditioning tokens before the tile sequence begins:
- Rightmost column of the already-approved left neighbor tile (x-1, y) — 16 tokens for a 16×16 tile
- Bottom row of the already-approved upper neighbor tile (x, y-1) — 16 tokens for a 16×16 tile

These boundary tokens are ground truth constraints, not generated. The model generates the new tile knowing exactly what palette indices must appear at its left and top edges, making seamless tiling a conditioning constraint rather than a post-hoc validation. Tileset generation must proceed in raster order (left-to-right, top-to-bottom) so neighbor tiles are always available. When a tile fails seam validation, the rebuild includes the same boundary conditioning plus a failure annotation describing the specific failed edge.

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

### 5.5b Prompt Expansion Layer (Optional — Character Modes Only)

The Prompt Expansion Layer is an optional step available in all character and NPC creation flows (Modes 1 and sheet extension requests). It converts a short description into a fully detailed character brief before generation begins.

**Problem it solves:**
A user who types "old wizard" gives the generation engine minimal guidance. The model fills gaps with statistical defaults — generic output that lacks the specific personality and visual anchors that make pixel art characters memorable.

**User flow:**
1. User opens New Character, types a short description: *"old wizard"*
2. User clicks **Expand** button (or types `/expand`) in the chat input
3. System sends the description to a language model with a structured expansion prompt
4. Expanded brief is returned and displayed in an editable text area, pre-filling the DNA brief fields:
   - `personality`, `role`, `defining_trait`
   - Visual anchors: clothing, accessories, color associations, posture, expression
5. User edits the expansion freely before confirming — it is a suggestion, not a decision
6. Confirmed expansion becomes the brief that feeds generation

**Example:**
Input: *"old wizard"*

Output: *An elderly male wizard, deeply stooped from decades hunched over spell books. Long silver beard with a slight yellow tinge at the tips. Midnight blue pointed robe, fraying at the hem, faded gold star embroidery barely visible. Worn leather belt with a cracked potion vial glowing amber at the hip. Skeletal hands with prominent knuckles, ink-stained fingertips. Deep-set eyes under heavy brows — wise but perpetually exhausted. Gnarled oak staff, twisted asymmetrically, topped with a cloudy crystal that pulses faintly.*

**Style bible guardrails (REFINEMENT-002A):**
The expansion system prompt must explicitly forbid anachronistic and non-SNES-appropriate details. Without this, expansion models drift toward modern aesthetics — glowing neon, cyberpunk elements, gradients, hyper-detail — that are incompatible with the style bible and produce unworkable generation inputs. The expansion prompt must include negative constraints: no glowing effects, no gradients, no modern materials, no sub-pixel detail that couldn't survive at 1× scale, palette color count awareness. Descriptions must represent characters a SNES-era studio could have actually shipped.

**Implementation:**
- Standard language model API call with structured system prompt
- System prompt is aware of the project's active genre and style bible
- The expansion button is visible in the chat input area only when in character/NPC creation mode
- Freeform Mode 7 does not use the expansion layer
- Built during Phase 7 — not required for Practice Gauntlet

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
6. On approval: exported as standalone PNG to `freeform/` — no DNA extracted, no manifest updated, no git commit to project state
7. Freeform outputs are logged in `logs/freeform_log.md` for reference only

**Implementation notes:**
- `pipeline/modes/mode7_freeform.py` handles this mode
- Freeform uses the same underlying transformer but without DNA conditioning tokens
- Resolution is specified by user — system validates it is a reasonable pixel art size (max 256x256 recommended; larger sizes supported but quality warning issued)
- Freeform outputs cannot be promoted to project assets without going through Mode 1 character creation to extract proper DNA

---

## 6. Project Organization

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

- Every sprite evaluated by the automated gate before the human ever sees it
- Automated gate scores 85 hard-math points — a sprite must pass 85/85 to be presented to the human
- Human scores the remaining 15 points (Originality and Soul/Visual Hierarchy) in the approval UI
- Combined score must reach 95/100 for final approval — below 95 means rebuild
- Cannot rationalize a flaw as a stylistic choice
- Cannot compare to its own earlier work — compares only to best work in reference library
- No partial credit for effort or complexity
- Every rejection documents specific, technical failure points
- Every pass documents what succeeded — added to `LESSONS_LEARNED.md`

### 8.3 The Three Rubrics

**Different asset types require different evaluation criteria.** A single rubric cannot evaluate characters, tilesets, and parallax backgrounds with equal accuracy. Three rubrics are defined. The correct rubric is selected automatically based on asset type.

---

#### Rubric A — Character / Enemy / Portrait / Effect Sprites

Applies to: all character profiles, NPC sprites, enemy sprites, portrait art, boss sprites, battle effects.

**Tier 1 — Automated Gate (85 points):** Scored by `rubric_scorer.py` and supporting tools. Sprite is not presented to the human until this passes 85/85.

| Category | Points | Evaluated By |
|----------|--------|--------------|
| Technical Compliance | 25 | `palette_validator.py`, `anti_aliasing_detector.py` |
| Construction Quality | 25 | `banding_detector.py`, `outline_checker.py`, `dna_diff.py` |
| Readability | 20 | Silhouette contrast analysis, pixel-level legibility checks |
| Animation Quality | 15 | `effect_timing_evaluator.py` (effects); pose consistency check (walk cycles) |
| **Automated Gate** | **85/85** | **Sprite presented to human only if this passes** |

**Tier 2 — Human Gate (15 points):** Awarded by the human in the approval UI. These criteria require semantic judgment that Python heuristics cannot provide reliably.

| Category | Points | Notes |
|----------|--------|-------|
| Originality | 10 | Does this feel fresh or is it a direct copy of a known sprite? |
| Soul / Visual Hierarchy | 5 | Context-dependent — see below |

**Context-aware Soul scoring (REFINEMENT-013A):**
Before scoring, the human declares the character's role in the approval UI:

- **Foreground** (player character, named NPC, boss, villain, party member): Soul scored as personality and distinctiveness. 0 = forgettable, 5 = memorable after one encounter.
- **Background** (generic townsperson, crowd NPC, ambient filler): Criterion renamed **Visual Hierarchy**. Scored as successful visual recession. 0 = competes with foreground characters for attention, 5 = reads clearly as background, never draws the eye away from named characters.

This distinction is intentional design craft. A named character that is forgettable is a failure. A townsperson that is too distinctive is also a failure — it undermines the visual hierarchy that makes named characters stand out. Both extremes are wrong. The role declaration also informs Originality scoring: a generic townsperson is expected to look somewhat generic and should not be penalized for resembling other background characters.

**Combined passing threshold: 95/100.** A sprite scoring 85/85 automated + 10+/15 human passes. Below 95 combined = rebuild.

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
- `vlm_critic.py` — **upgrade path only (CHANGE-021).** If automated heuristics produce systematic false positives above 10% (e.g., banding detector flags legitimate cylindrical shading, outline checker fails a character wearing a black robe), this tool supplements deterministic checks with a VLM API call for contextually ambiguous cases. Returns structured JSON: `{criterion, pass, violations, confidence}`. Only invoked on borderline cases, not every sprite. Initialized as a stub in Phase 0; implemented in Phase 5 only if false positive rates warrant it.

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

**Step 0 — Re-anchor (REFINEMENT-025A):** Read `am-pixel/CONSTITUTION.md` in full. Output a single sentence confirming all nine rules are in active context before the cycle continues. If any rule required re-reading the SPEC, note that. Write `logs/decision_log.md` entry if any rule required re-reading.

**Step 0b — Decision log catch-up (CHANGE-027):** Review `logs/decision_log.md` for the previous five-sprite cycle. Add entries for any quality or process decisions made during that cycle that were not logged at the time.

1. Rebuild the weakest sprite in the full project set
2. Extract lessons from the strongest sprite
3. Search for new pixel art resources — integrate if quality threshold met
4. Review and update `MISTAKE_TAXONOMY.md`
5. Approved production assets added to fine-tuning dataset

**Step 3b — Failure cluster review (CHANGE-031):** If the **running pass rate** (recent production batch) is **below 90%**, categorize failing sprites by rubric category and asset type, log the cluster analysis in `logs/training_log.md`, select one targeted intervention, and apply the **maximum escalation rule:** three consecutive diagnosis cycles without batch improvement → document in `logs/BLOCKERS.md` for human review.

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

## 13. User-Facing Web Interface

AM Pixel is operated through a local web UI served by FastAPI. This is not optional — it is a required deliverable. A solo developer cannot be expected to run Python scripts in a terminal to approve sprites. The web UI is the product's face.

### 13.1 Requirements

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

### 13.2 Technical Implementation

- **Server:** FastAPI serving both the inference API and the web UI
- **Frontend:** Single-page HTML/JS application — no external framework dependencies required; keep it simple and functional
- **Entry point:** `ui/app.py`
- **Templates:** `ui/templates/` — HTML templates
- **Static assets:** `ui/static/` — CSS and JS
- **Local only:** Web UI serves on localhost only (127.0.0.1) — never exposed to external network in local mode
- **Server mode:** In production deployment, UI is replaced by a proper client application calling the server-side inference API

### 13.3 Build Priority

The web UI skeleton (working chat panel + image preview + approve/reject controls) must be complete and functional before the Practice Gauntlet begins. OpenClaw cannot validate the approval workflow without a working UI to validate it through.

---

## 14. Technical Stack

- **Model:** Custom PyTorch transformer, universal hardware support via PyTorch device abstraction
- **Hardware:** Universal — detected automatically at startup via `model/hardware/detector.py`. Detection hierarchy:
  1. NVIDIA GPU → CUDA (fastest; preferred for training)
  2. AMD GPU → ROCm (PyTorch-supported; near-equivalent performance)
  3. Apple Silicon → MPS — Metal Performance Shaders (PyTorch M1/M2/M3 support)
  4. Other GPU → OpenCL via PyTorch extensions
  5. No GPU → CPU (inference is usable at **1–10 tokens/sec**; training at Phase 4 corpus scale is **measured in months** on CPU — **cloud GPU is required** for CPU-only machines; see ROADMAP Phase 4 Hardware Reality Check for tier estimates)
  - Cloud GPU rental (RunPod, Vast.ai, Lambda Labs) **required** for Phase 4 training on CPU-only hardware; budget and timing per ROADMAP
  - All device references in code route through the detection utility — no hardcoded `"cuda"` strings anywhere
- **Image tooling:** Pillow for pixel-level manipulation and validation
- **Sheet management:** Custom Python tools using layout manifests
- **Project state:** JSON manifests + Markdown human-readable files
- **Version control:** Git — every approval event is a commit
- **API layer:** FastAPI (inference endpoint + web UI server)
- **Web UI:** FastAPI + plain HTML/JS (localhost only in local mode)
- **Training data management:** Custom curation pipeline with quality scoring

---

## 15. Training Data Provenance

**`data/TRAINING_PROVENANCE_MANIFEST.json`** is an immutable ledger of every sprite that has entered the training pipeline. It is initialized in Phase 0 and never deleted. Every entry records: sprite ID, source URL, creator, license, license URL, date added, perceptual hash, copyright filter status, and tier (1 = Golden Dataset, 2 = broad corpus).

**This manifest is a legal shield.** If AM Pixel is ever challenged on copyright grounds, the manifest is the evidence that the model was trained exclusively on clean, permissively licensed material. Deleting training data does not retroactively legalize training — it eliminates the defense. See CHANGE-023 for the full legal rationale.

**Acceptable licenses:** CC0, CC-BY (any version), CC-BY-SA (note share-alike obligations), commissioned work-for-hire (copyright explicitly transferred), procedurally generated (post-MVP fine-tuning only). Not acceptable: CC-BY-NC (AM Pixel has commercial tiers), CC-BY-ND (training creates derivatives), unknown license.

A sprite without a manifest entry does not get trained on. No exceptions.

---

## 16. Post-MVP Architecture Evolution

**Component Compositing (CHANGE-022):**
The current flat-generation architecture generates sprites as fully composited pixel sequences. A component-based architecture — where a character is assembled from independently generated layers (base body, clothing, accessories, held items) — would solve the backpack problem more elegantly and make character customization trivial. DNA would become a node graph of attached components with defined attachment points rather than a flat pixel specification.

This is the right long-term direction. It is not MVP scope. The flat-generation architecture ships first. Component compositing is evaluated after Genre 1A production threshold is met, specifically if brief-conditioned multi-view generation (CHANGE-016) proves insufficient in practice.

A stub `model/architecture/COMPONENT_COMPOSITING_NOTES.md` is initialized in Phase 0 for reference.

---

*AM Pixel Specification v1.5 | Absentmind Studio*

---

## Changelog

### v1.5 — 2026-04-21
- **CHANGE-025–031, REFINEMENT-025A:** CONSTITUTION cross-refs; compliance layer in §3.3; DNA rollback procedure + cost warning (§4.3); versioned DNA filenames (§4.4); Continuous Training Protocol — re-anchor, decision log catch-up, failure cluster / escalation (§9.3); CPU training reality + cloud GPU (§14).

### v1.3 — 2026-04-12
- **CHANGE-010:** §3.1 — 2D positional encoding requirement added. 1D encodings (sinusoidal or RoPE) encode sequence distance, not canvas proximity — incompatible with structure-aware token ordering which scrambles spatial sequence position. Each token embedding now sums three components: palette index embedding + learned X coordinate embedding + learned Y coordinate embedding. DNA conditioning tokens use a separate learned embedding type and do not carry canvas coordinates.
- **CHANGE-011:** §3.4 — MaskGIT documented as Phase 4 optional speed experiment only; not a pre-Phase-0 architectural decision. Speed is explicitly not a primary project concern. Only triggered if batch generation is a demonstrated practical blocker. See README.md On Speed vs. Accuracy.
- **CHANGE-012:** §5.3 — Sliding window boundary conditioning added for tileset generation. Right edge of approved left neighbor + bottom row of approved upper neighbor prepended as hard conditioning tokens before each tile generation sequence. Tileset generation must proceed in raster order. Failed seam rebuilds include failure annotation describing the specific failed edge.
- **CHANGE-013 + REFINEMENT-013A:** §8.2/§8.3 — Rubric A restructured into two tiers. Tier 1: automated gate (85 points — Technical Compliance 25, Construction Quality 25, Readability 20, Animation Quality 15). Tier 2: human gate in approval UI (15 points — Originality 10, Soul/Visual Hierarchy 5). Soul criterion now context-aware: foreground characters (player, named NPC, boss) scored on personality and distinctiveness; background characters (generic townspeople, crowd fillers) scored on successful visual recession, criterion renamed "Visual Hierarchy" to reflect inverted goal. Passing threshold remains 95/100 combined.
- **CHANGE-014:** §3.2 — Pixel classifier simplified to four categories for foundation training: transparent, outline, structural, non-structural. Shade/detail boundary is semantically ambiguous in scraped sprite data — a highlight on armor could be either, causing inconsistent token ordering and degraded training signal. Full five-category classification deferred to fine-tuning set via `--full-five-category` flag in pixel_classifier.py.
- **CHANGE-015:** §3.4 Risk C — Skeletal pose tokens added as secondary animation upgrade path supplement. Rule-based 2D skeleton extraction (~10–12 key points per frame). Frame 2 conditioned on DNA + Brief + Frame 1 skeleton tokens (not raw pixel tokens) — gives model explicit positional deltas, not pixel values, avoiding copy pressure. Only build if raw-token temporal conditioning demonstrably fails. pose_extractor.py stub initialized Phase 0.
- **CHANGE-016:** §4.1, §4.2, §4.3, §4.4, §5.1 — Brief elevated from flavor text to required complete feature inventory. `occluded_features` array field added to DNA schema to record every feature not visible in the master sprite (backpacks, ponytails, rear armor, tails, wings). DNA lock warning updated to explicitly prompt for hidden feature completeness before locking. DNA extraction process prompts user for occluded features after pixel extraction. Mode 1 non-master profile generation updated to twin input: `[DNA] + [Complete Brief including occluded_features] + [Master View Tokens]` — DNA provides color/style identity, Brief ensures hidden features appear in side/rear views, Master View Tokens provide visual grounding.
- **CHANGE-017:** §3.2 — Paired-view training sequences added. view_pair_detector.py identifies candidate view pairs within sprite sheets via palette similarity and proportion matching. pair_annotator.py presents candidates for human confirmation. Confirmed pairs stored with view_pair_id and direction labels. Training format: `[DNA] + [Brief] + [View A Tokens]` → `[View B Tokens]`. Target: minimum 20% of training examples as paired-view sequences. Synthetic pairs (reflections) permitted at lower training weight.
- **CHANGE-018:** §Changelog — Changelog section added to document.
- **CHANGE-019:** §3.2 — Two-tier corpus strategy documented. Tier 1 = Golden Dataset: 3,000–5,000 manually curated, individually verified sprites stored in `data/golden/`; every sprite human-reviewed; primary quality signal for Stage 2 fine-tuning. Tier 2 = broad corpus: algorithmically scraped 30,000–50,000 sprites; used for Stage 1 foundation training. Phase 3 time allocation 3× original estimate warning added — manual curation cannot be automated or rushed.
- **CHANGE-021:** §8.4 — vlm_critic.py added as upgrade-path-only tool in tooling list. Supplements deterministic heuristics for contextually ambiguous criteria (e.g., banding detector falsely flagging cylindrical shading on a metal pipe; outline checker failing a character wearing a black robe). Returns structured JSON: `{criterion, pass, violations, confidence}`. Only invoked on borderline automated failures, not every sprite. Stub initialized Phase 0; implemented Phase 5 only if false positive rates exceed 10%.
- **CHANGE-022:** §16 Post-MVP Architecture Evolution added — component compositing documented as long-term right direction for the Backpack Problem and character customization. Flat generation ships first. Component compositing triggered only if brief-conditioned multi-view generation proves insufficient after Genre 1A. COMPONENT_COMPOSITING_NOTES.md stub initialized Phase 0.
- **CHANGE-023:** §15 Training Data Provenance added — TRAINING_PROVENANCE_MANIFEST.json documented as immutable legal ledger. Legal rationale: deletion does not retroactively legalize training; model weights are evidence subject to discovery; deleting data after becoming aware of copyright risk constitutes spoliation of evidence; EU AI Act requires training data documentation for commercial providers. Acceptable license types defined (CC0, CC-BY, CC-BY-SA, commissioned, procedurally generated). Retention policy: never delete manifest or Golden Dataset.
- Fixed duplicate training data sourcing priority section in §3.2 (appeared twice due to editing artifact).
- **Path corrections:** §5.7 freeform output path corrected from `assets/freeform/` to `freeform/` (root-level directory per FOLDER_STRUCTURE.md). §4.4 and §5.2 path corrected from `CHARACTER_DNA/` to `dna/characters/`. §5.2 corrected from `SHEET_LAYOUT/` to `sheets/`. §3.2 stale cross-reference corrected from `§3.2 Provenance Manifest` to `§15 Training Data Provenance`. Mode 6 `### 5.6` header restored (was missing — content existed without section heading).

### v1.3 — 2026-04-19
- Working-tree hygiene only: repo umbrella `README.md`, archive folder naming (`bible-v1.1` … `bible-v1.3-latest`), and `am-pixel/README.md` / `SPEC.md` version parity check. No technical specification content change.

### v1.4 — 2026-04-19
- Bible **v1.4** (per Bible-wide version rule): the canonical tree that diverges from the frozen **`bible-v1.3-apr13`** snapshot is no longer co-numbered as v1.3; all headers/footers set to **1.4**; archive folder **`bible-v1.4`**. No additional technical specification delta beyond version alignment in this entry.

### v1.2 — 2026-04-11
- **CHANGE-004:** Restored missing `## 6. Project Organization` header — subsections 6.1, 6.2, 6.3 were orphaned with no parent heading.
- **CHANGE-004:** Renumbered sections — Web UI moved from §14 to §13, Technical Stack from §15 to §14. No section 13 gap remains.
- **CHANGE-003:** §3.1 — Removed "NVIDIA GPU with CUDA, minimum 10GB VRAM" hardware requirement. Replaced with reference to universal detection hierarchy in §14.
- **CHANGE-003:** §14 Technical Stack completely rewritten with full detection hierarchy: NVIDIA→CUDA, AMD→ROCm, Apple Silicon→MPS, other GPU→OpenCL, no GPU→CPU. Cloud GPU rental note added for CPU-only training runs.
- **CHANGE-001 + REFINEMENT-001A:** §3.2 — Structure-aware token ordering added. Five pixel categories: transparent (first — commits alpha mask), outline, fill (base regions), shade (light ramps), detail (last — small features). Positional encodings preserve original (x,y) canvas coordinates. Phase 4 comparison experiment required (structure-aware vs raster). Category distribution logging required; flag any category below 3%.
- **CHANGE-007 (Risk A):** §3.4 — Sequence length error accumulation documented. Describes compounding prediction error problem at 3,072 tokens (48×64 battle sprite). Phase 4 gate: if >1,500 token pass rate < 70%, implement hierarchical generation before Phase 5. Hierarchical generation described as upgrade path.
- **CHANGE-008 (Risk B):** §3.4 — DNA conditioning dilution at long sequences documented. Attention signal weakens over 3,072 tokens. Phase 4 measurement: top-half vs bottom-half DNA consistency delta via dna_diff.py. Cross-attention upgrade path if delta consistently > 10%.
- **CHANGE-009 (Risk C):** §3.4 — Animation temporal coherence gap documented. Frame-independent generation enforces character continuity but not motion continuity. Phase 7–8 evaluation gate before temporal conditioning is built. Temporal conditioning upgrade path documented (previous frame tokens as conditioning input).
- **CHANGE-002 + REFINEMENT-002A:** §5.5b — Prompt Expansion Layer added as optional character creation step. LLM API call converts short description to full DNA brief. Expand button visible only in character/NPC modes. SNES style-bible guardrails in expansion system prompt (no neon, gradients, modern materials, sub-pixel detail). Always editable before confirmation. Freeform Mode 7 excluded. Built Phase 7.
- §3.3 Approval Pipeline row updated to note optional prompt expansion capability.

### v1.1 — 2026-04-11
- Product definition updated to include freeform generation capability.
- §3.3: Added Freeform Engine and Web UI as first-class system components.
- §3.1: Added Mode 7 freeform bypass note — no DNA conditioning, full 256-color vocabulary, outputs PNG only, never touches continuity manifest.
- §4.3: DNA Lock Warning scoped to Modes 1–6 only — Mode 7 explicitly non-DNA.
- Mode 7 Freeform (§5.7) added — full spec: bypasses DNA/style bible/SNES constraints, full 256-color palette, any user-specified resolution, lighter quality check, anti-pattern detector still runs, outputs to `freeform/` (root-level) only, max recommended 256×256, cannot be promoted to project assets without Mode 1 redesign. (Note: original doc said `assets/freeform/` — corrected to `freeform/` in v1.3 path audit.)
- §13 (now §13 after renumber) Web UI added — chat panel, 1×/4× sprite preview, approve/reject/adjust controls, project tabs, freeform tab, continuity manifest viewer, hardware status bar, FastAPI + plain HTML/JS, localhost only, web UI skeleton required before Practice Gauntlet.
- Technical stack updated: cloud GPU fallback note, FastAPI web UI as primary interface.
- Portrait profile added to Mode 1 (48×48–64×64, expression variants, max 4 unique detail colors).
- Large-format/multi-tile boss mode added to Mode 1 (multi-tile composition, sync animation, tile grid manifest).
- Mode 3 renamed to "Environment, Tileset & Parallax Generation."
- Tileset Anchor system added to Mode 3 (locked seed tiles governing all subsequent tile generation).
- Seam validation requirement added to Mode 3 (all four edges mandatory).
- Transition tiles added as explicit required tile type in Mode 3.
- World map location markers added to Mode 3.
- Mode 3b parallax background spec added — layer stack (sky/far/mid/foreground), Parallax Anchor, layer_compositor.py evaluation, character contrast check.
- Mode 4 expanded: status condition icons, element icons, item/equipment icon system with category grammar validation, world map location markers, title screen as special UI mode.
- Mode 6 Battle Effect Animations added as named mode.
- Tab structure updated to include Battle Effects, Portrait Art, Location Markers, all icon types, Title Screen.
- Single rubric replaced with three rubrics: Rubric A (characters/enemies/portraits/effects), Rubric B (tilesets — seam integrity 30pts as primary), Rubric C (parallax — layer depth differentiation 25pts as primary).
- Tooling added: seam_validator, tileset_anchor_extractor, layer_compositor, effect_timing_evaluator, icon_grammar_checker.

### v1.0 — Original Release
- Product definition: custom autoregressive transformer generating palette-index tokens — not a wrapper around existing image generators.
- Quality standard: 95/100 individual threshold, 99/100 production threshold (threshold definition was ambiguous at this version — ⚠️ CRITICAL DEFINITION callout added between v1.0 and v1.1).
- Core architecture: transformer decoder, DNA conditioning via prefix tokens, CUDA-only hardware requirement.
- Character DNA system: full schema, lock warning, extraction process.
- Generation modes 1–5: character creation, sheet extension, tileset/environment, UI, font.
- Single evaluation rubric covering all asset types.
- Project organization: tab structure, GitHub integration, multi-project DNA.
- Continuity enforcement: three checks, continuity manifest.
- Self-training layer: boot training, practice gauntlet, continuous protocol.
- Style modes: SNES default, hardware constraint toggle, future style expansion path.
- Export formats: Godot, RPG Maker MZ, GameMaker, Unity, generic JSON.
- Deployment: local mode, server mode, freemium tiers.
- Technical stack: CUDA-only.
