# Absentmind Studio (AM Studio)

> AI-powered retro game asset generation for solo developers and indie teams.

---

## What Is AM Studio

AM Studio is a suite of AI tools that gives solo game developers a complete art and audio department — no artistic skill required. Every tool in the suite is purpose-built for retro game aesthetics, producing original, studio-quality assets through natural language conversation.

AM Studio is not a wrapper around existing image generators. It is a custom-built AI pipeline with purpose-designed model architecture, character DNA enforcement, and a self-improving training loop. The output is indistinguishable from human-produced retro game art.

---

## The Suite

### AM Pixel *(active development)*
AI sprite generator and game asset manager for retro pixel art games.

- Text-to-sprite generation with iterative natural language approval
- Character DNA system for pixel-perfect cross-sprite continuity
- Full sprite sheet management (non-destructive extension)
- Environment tileset generation with aesthetic proof workflow
- Parallax battle background generation with layer system
- Battle effect animation generation (Mode 6)
- UI, font, and animated tile generation
- **Freeform generation (Mode 7)** — any custom pixel art image, any resolution, no project constraints
- Full local web UI — chat, preview, approve/reject, project tabs, freeform tab
- GitHub project integration and asset versioning
- Export for Godot, RPG Maker MZ, GameMaker, and generic JSON

[→ Full Specification](am-pixel/SPEC.md)
[→ Execution Roadmap](am-pixel/ROADMAP.md)

---

### AM Audio *(planned — post AM Pixel v1)*
AI chiptune composer and sound effects studio for retro game audio.
Planned as a companion to AM Pixel under the AM Studio umbrella. Not in current scope — development begins after AM Pixel reaches production threshold.

---

## Target User

Solo indie developers building retro-style games who have no art or audio skills and cannot afford a dedicated artist or composer. AM Studio removes the asset creation bottleneck entirely, replacing it with a natural language conversation.

---

## Brand

**Absentmind Studio** is the umbrella brand.
**AM Pixel** and **AM Audio** are the products.
The short form **AM Studio** is the everyday reference.

---

## Repository Structure

```
absentmind-studio/
├── README.md                  ← You are here
├── am-pixel/
│   ├── CONSTITUTION.md        ← Nine non-negotiable rules (read first)
│   ├── SPEC.md                ← Full technical specification
│   ├── ROADMAP.md             ← Phased execution plan with quality gates
│   ├── GENRE_TAXONOMY.md      ← Genre list, tiers, mastery definitions
│   ├── FOLDER_STRUCTURE.md    ← Complete on-disk layout
│   ├── OPENCLAW_PROMPT.md     ← Prompt to initialize OpenClaw execution
│   └── …                      ← model/, data/, pipeline/, tools/, etc.
└── am-audio/
    └── (planned)
```

---

## Branch Structure

The `main` branch is the clean-data production lineage — all training data is permissively licensed; all quality and legal rules apply in full. Transformative research branches (named `*/enable-all-sprites-training-*` or similar) are a separate, air-gapped research track governed by `TRANSFORMATIVE_BRANCH_NOTICE.md`. They are never merged here. See `am-pixel/CONSTITUTION.md` Rule 10.

---

## Status

AM Pixel Bible documents are at **v1.5** (`CONSTITUTION`, `SPEC`, `ROADMAP`, `FOLDER_STRUCTURE`, `OPENCLAW_PROMPT`, `GENRE_TAXONOMY`, `am-pixel/README.md`). **PROPOSED_CHANGES_001** and **Series 002** are merged into the Bible (archives retained). **PROPOSED_CHANGES_003** (drift prevention, compliance gates, session logs) is merged into v1.5; the file remains as a proposal archive. OpenClaw should begin from `am-pixel/CONSTITUTION.md`, then `am-pixel/OPENCLAW_PROMPT.md`. This remains a living document set.

---

## Changelog

### v1.5 — 2026-04-21
- Bible **v1.5**: Series 003 — CONSTITUTION.md, compliance tooling, session/decision logs, Startup Protocol (Rule 11), hardware reality table, DNA rollback procedure, Phase 8 failure-cluster protocol.

### v1.4 — 2026-04-19
- Bible **v1.4**: per Document Hygiene Rules, canonical post-`bible-v1.3-apr13` revision is no longer labeled v1.3; Status and all `am-pixel` headers/footers updated; archive folder **`bible-v1.4`**

### v1.3 — 2026-04-19
- Status aligned to Bible v1.3; clarified PROPOSED_CHANGES_001 (archived) vs PROPOSED_CHANGES_002 (staging)

### v1.2 — 2026-04-11
- Updated Status: removed "gap-free" language, updated version reference, noted living document approach

### v1.1 — Original release
- Initial document

---

*Built by Absentmind. The neverending project that ships.*
