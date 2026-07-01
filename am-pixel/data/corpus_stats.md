# Corpus Statistics

Report **Tier 1** (Golden) and **Tier 2** (broad corpus) separately — CHANGE-019 / CHANGE-023.

## 2026-07-01 — Tier 0 validation corpus (CHANGE-037; excluded from production statistics)

- Sprites: 300 (240 character-form, 60 seamless tiles), procedural, seed 7
- Provenance: 300/300 manifest entries (tier 0, license synthetic-validation), journal-first writes
- Pixel category distribution (4-category): {'transparent': 0.4192, 'outline': 0.1945, 'structural': 0.3521, 'non_structural': 0.0343}
- Categories below the 3% floor: none — note: 'non_structural' rides near the floor
  because procedural sprites have limited detail pixels; REAL corpora must be re-checked
  against this gate in Phase 3 (ROADMAP)
- Split (deterministic, pair-aware): ~90/10 train/validation

Tier 1: 0 sprites (network-blocked in this environment — see logs/BLOCKERS.md)
Tier 2: 0 sprites (same)
