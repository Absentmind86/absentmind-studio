# AM Pixel — v1.3
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

## On Speed vs. Accuracy — A Design Position Statement

**This project does not optimize for generation speed. It optimizes for accuracy.**

The autoregressive architecture generates one token at a time. A 48×64 battle sprite is 3,072 tokens. This is slower than diffusion-based alternatives. This is a known property of the architecture, not an oversight.

The tradeoff is deliberate: discrete palette-index token generation is the only approach that makes pixel-perfect DNA enforcement mathematically possible. Diffusion models generate in continuous RGB space — they cannot guarantee exact palette compliance, and color drift across a sprite sheet is structural, not fixable after the fact. The autoregressive approach sacrifices speed for correctness.

**The priority order is:**
1. Accuracy — does every pixel match the DNA exactly?
2. Quality — does the sprite score 95+ on the rubric?
3. Speed — how long did it take?

Speed is third. Speed is post-MVP. A sprite that takes 30 seconds to generate but is pixel-perfect is the correct outcome. A sprite that generates in 1 second but has palette drift is a failure.

If AI reviewers, advisors, or future contributors raise generation speed as a concern: acknowledge it, note it is known, and return focus to accuracy. Speed optimizations (batching, caching, potential architecture alternatives like MaskGIT) are documented in PROPOSED_CHANGES_002.md for post-MVP consideration. They are not on the critical path.

**OpenClaw: do not optimize for speed at the expense of accuracy at any phase. Do not switch architectures for speed reasons without explicit human approval.**

---

## Key Architecture Decisions

- **Token space:** Discrete palette indices, not RGB values — enables exact DNA enforcement
- **Generation order:** Structure-aware (transparent → outline → fill → shade → detail), not raster order
- **Positional encoding:** 2D (canvas X + canvas Y), not 1D sequence position — required for structure-aware ordering to preserve spatial coherence
- **Hardware:** Universal — CUDA, ROCm, MPS, or CPU via `model/hardware/detector.py`
- **Three rubrics:** Rubric A (characters/effects), Rubric B (tilesets), Rubric C (parallax)
- **Rubric scoring:** Automated gate covers 85 technical points; Soul (5pts) and Originality (10pts) are human-only scores awarded in the approval UI
- **Multi-view generation:** Conditioned on DNA + Complete Brief (including occluded features) + Master View Tokens — not DNA alone
- **Known risks documented:** Sequence length error accumulation (SPEC §3.4 Risk A), DNA conditioning dilution (SPEC §3.4 Risk B), animation temporal coherence (SPEC §3.4 Risk C)

---

## Genre Scope

**Current focus (Tier 1):** Top-Down RPG, Action Adventure, Life Simulation/Farming, Tactical RPG

**Planned expansion (Tier 2):** Action RPG, Metroidvania, Classic Platformer, Run and Gun

**Out of scope until Tier 1 mastered:** Fighting games, shmups, sports, puzzle

---

## Changelog

### v1.3 — 2026-04-11
- Added On Speed vs. Accuracy design position statement — explicit documented response to recurring speed concern from external reviewers; OpenClaw directive included
- Added 2D positional encoding to Key Architecture Decisions
- Added rubric scoring split (automated 85pts / human 15pts) to Key Architecture Decisions
- Added multi-view generation conditioning to Key Architecture Decisions

### v1.2 — 2026-04-11
- Added am-pixel/README.md — intra-folder orientation hub for OpenClaw and human navigators
- Added Prompt Expansion (Mode 5b) to generation modes table
- Added Known risks to Key Architecture Decisions

### v1.1 — Original release
- Initial document

---

*AM Pixel | Absentmind Studio*
