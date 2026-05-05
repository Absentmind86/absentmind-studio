# AM Pixel — Proposed Changes Series 004
**Transformative Branch Governance — T-Series**

This document defines policy for the transformative research branch. Unlike prior series, these changes apply **only to the transformative branch** and must never be merged into `main`. They are recorded here as the canonical rationale document for the T-series policy delta.

---

## Status

All T-series items are accepted and implemented on the transformative branch. This document is the permanent proposal archive — retained per Document Hygiene Rules.

---

## CHANGE-T01 — Transformative Branch Scope

**Document:** `TRANSFORMATIVE_BRANCH_NOTICE.md` (repo root, this branch only)
**Section:** New file

**What:** Establishes the boundary between this branch and `main`. Hard prohibitions: no merge, no weight distribution, no output crossover, no corpus crossover. Permitted purpose: capability ceiling research and A/B quality benchmarking against `main`.

**Why:** A parallel research track that uses unrestricted-license data requires a clear, durable governance boundary so that no artifact from this track can contaminate `main`'s legal lineage. The notice is the written record that both branches have actively acknowledged and documented the separation.

---

## CHANGE-T02 — License Allowlist Suspension (Transformative Manifest Only)

**Document:** `am-pixel/SPEC.md` §3.2, §15; `am-pixel/CONSTITUTION.md` Rule 5; `am-pixel/OPENCLAW_PROMPT.md` Rule 10; `am-pixel/ROADMAP.md` Phase 3
**Section:** Addenda in each document

**What:** On this branch, the license allowlist defined in SPEC.md §15 (CC0, CC-BY, CC-BY-SA, commissioned, procgen only) is suspended for entries written to `TRAINING_PROVENANCE_MANIFEST.transformative.json`. Any sprite source may be ingested regardless of license status.

The `copyright_filter_passed` field in the manifest is retained as an **observation** (true / false / unknown) rather than a gate — sprites are ingested either way but the field is populated honestly for dedup and analysis.

**What is NOT relaxed:**
- Manifest entry still required before ingestion (entry-before-write rule stands)
- Manifest is never deleted
- Site robots.txt and explicit scraping blocks are still respected
- No synthetic sprites as training data (circular signal problem is independent of license)
- No contributor outreach by OpenClaw (CHANGE-024 agent-scope prohibition stands)
- Mode 7 freeform outputs stay out of training (UX boundary, unrelated to licenses)
- All architecture, quality, evaluation, and hardware rules are unchanged

**Why:** This branch exists specifically to test whether a broader corpus produces measurably higher quality output than the clean-data `main` model. Suspending the license filter is the operational prerequisite. The separation into a physically distinct machine (air-gapped mini PC) and a private repository on a separate account ensures that weight exposure, output distribution, and main-lineage contamination are structurally impossible regardless of what happens on this branch.

**Transformative manifest path:** `am-pixel/data/TRAINING_PROVENANCE_MANIFEST.transformative.json`
**Transformative corpus path:** `am-pixel/data/corpus_transformative/`
**Transformative scraper source log:** `am-pixel/data/scraper/sources_transformative.md`
**Transformative scrape run log:** `am-pixel/data/scraper/scrape_log_transformative.md`

---

## CHANGE-T03 — Parallel Manifest, Corpus, and Log Paths

**Document:** `am-pixel/FOLDER_STRUCTURE.md`
**Section:** data/ tree

**What:** New paths added to the folder structure (this branch only):
- `data/TRAINING_PROVENANCE_MANIFEST.transformative.json` — transformative-branch ledger
- `data/corpus_transformative/train/` — transformative Tier 2 training data
- `data/corpus_transformative/validation/` — transformative Tier 2 validation data
- `data/scraper/sources_transformative.md` — source log for transformative scraping
- `data/scraper/scrape_log_transformative.md` — run log for transformative scraping
- `logs/transformative_log.md` — A/B comparison notes, cross-branch decisions

The canonical paths (`data/corpus/`, `data/golden/`, `TRAINING_PROVENANCE_MANIFEST.json`, `data/scraper/sources.md`) are **unchanged**. Golden Dataset rules are not relaxed on this branch — Tier 1 remains commissioned/CC0 only.

**Why:** Physical separation of mutable data paths means there is no accidental commingling. Any script that reads from `corpus/` or writes to `TRAINING_PROVENANCE_MANIFEST.json` is operating on clean-data paths. Transformative operations must explicitly target the `_transformative` variants.

---

## CHANGE-T04 — Branch-Aware Compliance Gates

**Document:** `am-pixel/tools/compliance.py`, `am-pixel/tests/test_compliance.py`
**Section:** New functions

**What:** Two new functions added to `compliance.py`:
- `transformative_provenance_gate(sprite_id, manifest_path=...)` — same shape as `provenance_gate` but defaults to the transformative manifest path. Docstring explicitly marks it as transformative-branch-only.
- `training_run_gate_transformative(...)` — same shape as `training_run_gate` but reads from the transformative manifest. Does not check for `PHASE4_ARCHITECTURE_REVIEW: APPROVED` (the architecture review gate is preserved on both branches — architecture discipline is independent of data policy).

Existing functions (`provenance_gate`, `training_run_gate`) are **unchanged**. Their behavior is byte-identical to `main`. They continue to enforce the canonical manifest.

New tests in `test_compliance.py` cover both new gate functions.

Pre-commit banner updated with a line noting transformative gate variants.

**Why:** Keeping separate function names makes misuse structurally impossible — a developer on `main` cannot accidentally call a transformative gate. The existing gate's contract is provably unchanged (existing tests continue to pass).

---

## CHANGE-T05 — Rules Explicitly Preserved on This Branch

For clarity and to prevent future ambiguity, the following rules are unchanged on this branch and are documented here in canonical form:

| Rule | Source | Kept as-is |
|---|---|---|
| Manifest entry required before ingestion | CONSTITUTION Rule 5 / SPEC §15 | Yes — entry-before-write stands, only license filter suspended |
| Manifest never deleted | CONSTITUTION Rule 5 | Yes |
| Golden Dataset never deleted | CONSTITUTION Rule 5 | Yes |
| Respect robots.txt / explicit scraping blocks | OPENCLAW_PROMPT Training Data | Yes — TOS/CFAA risk is separate from copyright and out of scope |
| No synthetic sprites as training data | OPENCLAW_PROMPT Training Data | Yes — circular signal problem is independent of license policy |
| Mode 7 freeform outputs not added to training | SPEC §3.1, §5.7 | Yes |
| OpenClaw does not initiate contributor outreach | CHANGE-024 | Yes |
| No merge to main | CONSTITUTION Rule 10 / TRANSFORMATIVE_BRANCH_NOTICE.md | Yes |
| No weight distribution | TRANSFORMATIVE_BRANCH_NOTICE.md | Yes |
| No output crossover into main corpus or Golden Dataset | TRANSFORMATIVE_BRANCH_NOTICE.md | Yes |
| Architecture rules (autoregressive palette-index tokens only) | CONSTITUTION Rule 2 | Yes |
| Quality thresholds (95/100, 99/100 batch) | CONSTITUTION Rule 1 / SPEC §2 | Yes |
| Hardware detection (no hardcoded CUDA) | CONSTITUTION Rule 3 | Yes |
| Evaluation rubric (A/B/C, 85/85 automated gate) | CONSTITUTION Rule 4 | Yes |
| Human override authority | CONSTITUTION Rule 9 | Yes |
| Transformative branch boundary | CONSTITUTION Rule 10 | Yes |

---

*AM Pixel Proposed Changes Series 004 — Transformative Branch T-Series | Absentmind Studio*
*This branch only — never merged to main*
