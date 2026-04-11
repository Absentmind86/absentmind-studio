# AM Pixel
**Absentmind Studio — AI Sprite Generator & Game Asset Manager**

This folder contains the complete specification and execution documents for AM Pixel. If you are OpenClaw, read these documents in the order listed before doing anything else.

---

## Document Index

| Document | Purpose | Read Order |
|----------|---------|------------|
| [SPEC.md](SPEC.md) | Full technical specification — architecture, DNA system, all generation modes, evaluation rubrics, training pipeline | 1st |
| [ROADMAP.md](ROADMAP.md) | Phased execution plan — every task, every gate, in order | 2nd |
| [GENRE_TAXONOMY.md](GENRE_TAXONOMY.md) | Genre tiers, mastery definitions, progression rules | 3rd |
| [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) | Exact file and directory structure initialized in Phase 0 | 4th |
| [OPENCLAW_PROMPT.md](OPENCLAW_PROMPT.md) | The initialization prompt — contains confirmation requirements and non-negotiable rules | Already held |

---

## What AM Pixel Is

AM Pixel is a custom-built AI sprite generator for retro pixel art games. It produces original, studio-quality assets through natural language conversation with a character DNA system that enforces perfect visual continuity across an entire project.

It is not a wrapper around any existing image generator. It is a purpose-built autoregressive transformer that generates sprites as sequences of discrete palette-index tokens — the same architecture as a language model, applied to pixel art.

---

## Seven Generation Modes

| Mode | Name | What It Does |
|------|------|--------------|
| 1 | Character Creation | Text → sprite → DNA lock → full sprite sheet |
| 2 | Sheet Extension | Add animations to existing characters without touching existing sprites |
| 3 / 3b | Tileset & Parallax | Environment tilesets with aesthetic proof; layered parallax battle backgrounds |
| 4 | UI Generation | Curated style options → full UI asset set including icons and title screen |
| 5 | Font Generation | Curated pixel font options → full character set |
| 5b | Prompt Expansion | Optional: expand short descriptions into full character briefs (SNES style-aware) |
| 6 | Battle Effects | Animated spell, impact, and effect sequences for combat |
| 7 | Freeform | Unconstrained generation — any description, any resolution, no DNA, no style bible |

---

## Quality Standard

Every generated sprite is evaluated before the human sees it.

- **Individual threshold:** 95/100 on the evaluation rubric — below 95 means rebuild, not patch
- **Production threshold:** 99 out of 100 sprites in a validation batch must each independently score 95+ — this is a batch pass rate, NOT a score of 99 points

---

## Key Architecture Decisions

- **Token space:** Discrete palette indices, not RGB values — enables exact DNA enforcement
- **Generation order:** Structure-aware (transparent → outline → fill → shade → detail), not raster order
- **Hardware:** Universal — CUDA, ROCm, MPS, or CPU via `model/hardware/detector.py`
- **Three rubrics:** Rubric A (characters/effects), Rubric B (tilesets), Rubric C (parallax)
- **Known risks documented:** Sequence length error accumulation (SPEC §3.4 Risk A), DNA conditioning dilution (SPEC §3.4 Risk B), animation temporal coherence (SPEC §3.4 Risk C)

---

## Genre Scope

**Current focus (Tier 1):** Top-Down RPG, Action Adventure, Life Simulation/Farming, Tactical RPG

**Planned expansion (Tier 2):** Action RPG, Metroidvania, Classic Platformer, Run and Gun

**Out of scope until Tier 1 mastered:** Fighting games, shmups, sports, puzzle

---

*AM Pixel | Absentmind Studio*
