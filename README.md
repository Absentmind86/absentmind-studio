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

- Text-to-sprite generation with iterative approval
- Character DNA system for perfect cross-sprite continuity
- Full sprite sheet management (non-destructive extension)
- Environment tileset generation with aesthetic proof workflow
- UI, font, and animated tile generation
- GitHub project integration
- Export for Godot, RPG Maker MZ, GameMaker, and generic JSON

[→ Full Specification](am-pixel/SPEC.md)
[→ Execution Roadmap](am-pixel/ROADMAP.md)

---

### AM Audio *(planned)*
AI chiptune composer and sound effects studio for retro game audio.
Planned as a companion to AM Pixel under the AM Studio umbrella.

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
│   ├── SPEC.md                ← Full technical specification
│   ├── ROADMAP.md             ← Phased execution plan with quality gates
│   ├── GENRE_TAXONOMY.md      ← Genre list, tiers, mastery definitions
│   ├── FOLDER_STRUCTURE.md    ← Complete project file structure
│   ├── OPENCLAW_PROMPT.md     ← Prompt to initialize OpenClaw execution
│   └── src/                   ← OpenClaw builds here
└── am-audio/
    └── (planned)
```

---

## Status

AM Pixel is in pre-development definition phase. All architectural decisions have been made. OpenClaw execution begins from `am-pixel/OPENCLAW_PROMPT.md`.

---

*Built by Absentmind. The neverending project that ships.*
