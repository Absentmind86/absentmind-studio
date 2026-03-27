# AM Pixel — Genre Taxonomy
**Absentmind Studio | Version 1.1**

---

## Overview

This document defines the genre taxonomy for AM Pixel's progressive training roadmap. Genres are organized into tiers based on asset similarity and training complexity. The system progresses through tiers sequentially — advancing only after hitting the 99/100 production threshold in the current tier.

The goal is not to eventually support every genre ever made. The goal is to achieve genuine mastery in a defined set of genres that share meaningful asset overlap. Scope discipline is what makes the tool exceptional rather than mediocre at everything.

**Freeform generation (Mode 7) is genre-agnostic and always available.** It does not count toward any genre mastery threshold, does not affect the continuity manifest, and does not interact with the tiered training progression in any way. It is the escape hatch for one-off custom images that fall outside any defined genre or project scope. See SPEC.md §5.7 for full Mode 7 specification.

---

### ⚠️ CRITICAL DEFINITION — WHAT "99/100 THRESHOLD" MEANS

The 99/100 production threshold is a BATCH PASS RATE. It is NOT a score of 99 points.

It means: **in a validation batch of 100 generated sprites, at least 99 individual sprites must each independently score 95 or above on the evaluation rubric.**

- 99 sprites each scoring 95+ out of 100 → THRESHOLD MET ✅
- 1 sprite scoring 99 points → THRESHOLD NOT MET ❌
- 98 sprites all scoring 100 points → THRESHOLD NOT MET ❌ (98 pass, need minimum 99)

This definition applies every time the 99/100 threshold is mentioned in this document.

---

## The Progression Model

Each genre within a tier shares significant asset overlap with others in the same tier. Training on one genre in a tier accelerates training on adjacent genres because the underlying pixel art principles — proportion, palette construction, environment design — transfer heavily.

**Advancement rule:**
In a validation batch of 100 generated sprites, at least 99 individual sprites must each independently score 95 or above on the evaluation rubric — without requiring a rebuild — before the system advances to the next genre. This batch is drawn evenly across all asset types for the genre (characters, enemies, tilesets, UI).

---

## Tier 1 — Primary Focus (Current)

These genres share the highest degree of asset similarity. Mastering one builds directly toward mastering all others in this tier. This is the only tier currently in active development.

---

### 1A. Top-Down RPG
**Reference games:** Final Fantasy IV, V, VI (SNES) — Earthbound — Dragon Quest V, VI

**Mastery definition:**
- Battle sprites: large format (48x64+), expressive animations, 6+ animation states per character
- World sprites: 16x24, readable personality at actual size
- Tilesets: interior (towns, inns, shops, castles) and exterior (wilderness, roads, bridges)
- World map tiles: simplified terrain — mountains, forests, plains, coast, ocean
- World map character sprite: chibi simplified version, 8x16
- UI: dialogue box, menu system, status screen, battle HUD
- Enemy sprites: varied archetypes from animal to humanoid to boss-scale creatures

**Asset types required:**
Characters, enemies, NPCs, interior tilesets, exterior tilesets, world map tiles, world map character sprites, battle backgrounds, UI, fonts, portrait art, animated tiles (water, lava, torches, flags)

---

### 1B. Action Adventure (Top-Down)
**Reference games:** The Legend of Zelda: A Link to the Past — Secret of Mana — Illusion of Gaia

**Mastery definition:**
Shares heavy overlap with 1A. Key differences:
- Character sprites optimized for fluid 8-directional movement
- More emphasis on environment interactivity (destructible objects, switches, pressure plates)
- Dungeon design language distinct from RPG dungeons — puzzle-oriented, trap-heavy aesthetics
- Item and pickup sprites (hearts, rupees, keys, bombs)
- Overworld designed for exploration rather than narrative nodes

**Asset types required:**
All of 1A plus: item/pickup sprites, interactive object states (open/closed/broken), dungeon puzzle elements, more extensive animated environment objects

---

### 1C. Life Simulation / Farming
**Reference games:** Harvest Moon: A Wonderful Life — Story of Seasons — Stardew Valley (as aesthetic reference)

**Mastery definition:**
- Seasonal tileset variants: same environment in spring, summer, autumn, winter
- Time-of-day palette variants: dawn, day, dusk, night for key environments
- Crop growth stages: 4-6 visual states per crop type
- Farm building sprites and construction stages
- Animal sprites: cow, chicken, sheep, horse — idle and animated
- Weather effects: rain, snow, wind-blown foliage
- Interior sprites: farmhouse rooms, shop interiors, villager homes
- Villager NPC variety: same-world feel across 20+ unique NPCs using archetype variant system

**Asset types required:**
All of 1A/1B plus: seasonal variants, crop sprites, animal sprites, weather effect tiles, NPC archetype variant system, farm building sprites

---

### 1D. Tactical RPG
**Reference games:** Final Fantasy Tactics — Tactics Ogre — Fire Emblem (SNES)

**Mastery definition:**
- Isometric tile perspective — distinct from top-down, requires understanding of isometric grid
- Unit sprites designed for isometric context — different proportion conventions
- Terrain tiles: isometric grass, stone, elevation changes, water, cliffs
- Battle map design language — readable height levels, clear grid definition
- Class-based character variety — same base sprite adapted across 20+ job classes
- Map interface elements: grid overlay, movement range indicators, attack range

**Asset types required:**
Isometric tilesets, isometric character sprites, job-class variant system, battle map UI elements

---

## Tier 2 — Natural Expansion (Post Tier 1 Mastery)

These genres require meaningful additional training but share enough asset overlap with Tier 1 that progression is natural. Do not begin any Tier 2 genre until all Tier 1 genres reach production threshold.

---

### 2A. Action RPG
**Reference games:** Secret of Mana, Terranigma, Actraiser, Illusion of Gaia

Closest to Tier 1. Adds: real-time combat sprite requirements (faster animation cycles, impact frames, dodge animations), more expressive boss designs, combo animation sequences.

---

### 2B. Metroidvania
**Reference games:** Super Metroid, Castlevania: Super, Castlevania: Dracula X

Adds: side-scrolling perspective (different from top-down — character sprites read differently), vertical environment design, atmospheric tileset conventions (gothic, sci-fi, subterranean), detailed parallax background requirements.

---

### 2C. Classic Platformer
**Reference games:** Super Mario World, Kirby Super Star, Donkey Kong Country

Adds: horizontal scrolling perspective, ground-plane tile conventions, platform and hazard design language, collectible and power-up sprite systems.

---

### 2D. Run and Gun Platformer
**Reference games:** Mega Man X, Contra III, Super Castlevania IV

Adds: action-optimized character animation (larger frame counts for fluid combat), hazard and projectile sprites, more complex enemy animation sets, boss design at larger scales.

---

## Tier 3 — Future Consideration (Not In Current Scope)

These genres require significantly different training, asset conventions, and evaluation criteria. They are documented here for future reference only. Do not develop toward these until AM Pixel has achieved production-quality mastery across all of Tier 1 and at least two Tier 2 genres.

- **Fighting game** (Street Fighter, King of Fighters) — Frame-precise animation, hitbox-readable poses, exaggerated proportions, extreme style divergence from RPG conventions
- **Shoot em up / shmup** (R-Type, Gradius) — Heavily mechanical sprite design, complex bullet pattern effects, scrolling environment requirements
- **Sports game** — Realistic human proportion requirements, sport-specific animation sets
- **Puzzle game** — Abstract tile design, specialized UI requirements

---

## The Blend Problem

Many games don't fit a single genre cleanly. Zelda is action-adventure with RPG elements. Harvest Moon is life simulation with RPG progression. This is handled at the project level — not the model level.

When a user declares their project context, they describe it naturally:

> *"I'm making a Zelda-style action adventure with some light RPG elements — towns with NPCs, shops, a simple leveling system."*

The system maps this to a primary genre (1B) with secondary influences (1A) and applies the appropriate asset conventions. It does not need a separate model for every possible blend. The genre taxonomy defines the training targets. The project declaration defines how to apply them.

For assets that fall completely outside any defined genre — abstract compositions, custom icons, concept art, or anything else that doesn't fit — use Mode 7 freeform generation. Freeform handles anything the genre system cannot.

---

## Genre Mastery Threshold

Each genre is considered mastered when:

1. 99/100 generated sprites across all asset types for that genre pass the 95/100 rubric without rebuild
2. A human evaluator familiar with the reference games cannot reliably distinguish AM Pixel output from original SNES-era studio work
3. `LESSONS_LEARNED.md` contains 20+ genre-specific rules derived from production experience (not research theory)
4. The genre's entry in this document is updated with specific notes on what was learned

---

*AM Pixel Genre Taxonomy v1.1 | Absentmind Studio*
