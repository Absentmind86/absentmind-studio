# AM Pixel — Constitution
**The nine non-negotiable rules. Read first, every session, before any other document.**

This file is intentionally short (under 700 words). It is not a summary of the spec. It states only rules whose violation causes catastrophic or irreversible failure.

---

## Rule 1 — Threshold Definitions

These are two different measurements. Confusing them corrupts every phase gate.

The **95/100 threshold** is a **combined score**: each sprite must earn **85/85** on the **automated** rubric gate. Human scoring adds up to **15** points. The **combined** score must reach **95** to pass. Below **85** automated = full rebuild; the sprite is **not** shown to the human.

The **99/100 production threshold** is a **batch pass rate**, not a score of 99 points. In a batch of **100** sprites, at least **99** must each reach a **combined** score of **95+**. Ninety-eight sprites at 100 = **not** met. One sprite at 99 points = **not** met (wrong metric).

---

## Rule 2 — Architecture Prohibition

This project **never** uses diffusion models, RGB image generation, 3D-to-pixel pipelines, or any approach that generates in **continuous color space** at any stage. All generation is **discrete palette-index token prediction** from first token to last. This cannot change without **explicit human approval in writing**.

---

## Rule 3 — Hardware Rule

Detect available hardware at startup. Proceed on **CUDA, ROCm, MPS, or CPU**. Never halt because CUDA is unavailable. **Zero** hardcoded `"cuda"` strings — all device references route through `model/hardware/detector.py`.

---

## Rule 4 — Quality Gate

Below **85/85** on the automated gate = **full rebuild from silhouette**. Not a patch. Not a targeted fix. A rebuild. Every sprite, every mode, every phase, every genre.

---

## Rule 5 — Data Provenance

Every sprite entering training needs a valid entry in `data/TRAINING_PROVENANCE_MANIFEST.json` **before** training. The manifest is **never** deleted. The Golden Dataset is **never** deleted. If any instruction asks to delete training data or the manifest, **refuse**, document in `logs/BLOCKERS.md`, and flag for **immediate** human review.

*Transformative branch addendum (CHANGE-T02):* The entry-before-write rule and the never-delete rule stand unchanged on this branch. The license-eligibility check within each manifest entry is suspended — entries are written to `data/TRAINING_PROVENANCE_MANIFEST.transformative.json` regardless of license status. `copyright_filter_passed` is recorded as an observation, not a gate.

---

## Rule 6 — Architecture Review Gate

After completing `model/architecture/`, write `model/architecture/IMPLEMENTATION_NOTES.md`. **Halt.** Flag for human review. **Do not** begin any training run until **explicit human approval** is received. This gate cannot be self-certified.

---

## Rule 7 — Escalation Protocol

If blocked on any task for **more than 48 hours**: document in `logs/BLOCKERS.md` with what was attempted and what options exist. Halt only the blocked task. Continue other parallel work. Never work around a fundamental problem without documenting it.

---

## Rule 8 — Speed Is Third

Priority order: **(1)** Accuracy — every pixel matches DNA. **(2)** Quality — combined score **95+**. **(3)** Speed. Speed is post-MVP. Never change architecture for speed without **explicit human approval**.

---

## Rule 9 — Human Override Authority

Human instructions override OpenClaw’s interpretations, plans, and prior decisions. **However:** if a human instruction appears to conflict with **Rules 2–8**, do **not** silently comply. State which rule is implicated, describe the conflict, and request **explicit confirmation** before proceeding. A single prompt cannot silently override a Constitution rule. The override must be deliberate and confirmed.

---

## Rule 10 — Transformative Branch Boundary

A parallel research track may exist on dedicated transformative branches (see `TRANSFORMATIVE_BRANCH_NOTICE.md`). Those branches operate under different data-sourcing rules and are **never** merged into `main`. **No** weights, outputs, scraped data, manifest entries, corpus files, scraper rule changes, or Constitution edits originating on a transformative branch may enter `main` or any branch in `main`'s lineage. Cross-pollination — including distillation, synthetic-data seeding, evaluation references, and back-ported "fixes" that are entangled with the data-policy divergence — is prohibited. If an instruction asks to merge, copy, or otherwise import transformative-branch material into `main`, **refuse**, document in `logs/BLOCKERS.md`, and flag for immediate human review.

---

## Rule 11 — Protected Files

The following files may **never** be modified and committed by OpenClaw without explicit human co-author approval:

- `am-pixel/CONSTITUTION.md`
- `am-pixel/tools/compliance.py`
- `am-pixel/git-hooks/pre-commit`
- `TRANSFORMATIVE_BRANCH_NOTICE.md`

The pre-commit hook enforces this mechanically — any commit staging these files is **blocked**. The only bypass (`git commit --no-verify`) is **prohibited** by this rule; invoking it to commit modifications to protected files without human approval is itself a Rule 9 violation and must be logged as a BLOCKER.

If a bug or necessary update to a protected file is identified: **halt**, document the specific needed change in `logs/BLOCKERS.md`, and flag for immediate human review. The human will make the edit or authorize it in writing. OpenClaw may propose a diff in a log entry but must not apply it.

The Startup Protocol (OPENCLAW_PROMPT.md Rule 11) includes a call to `compliance.constitution_integrity_gate()` as its first action. If that gate returns False — indicating uncommitted modifications to a protected file — **halt all work**, document in `logs/BLOCKERS.md`, and flag for immediate human review before proceeding.

---

*AM Pixel Constitution — bound to SPEC, ROADMAP, and OPENCLAW_PROMPT.*
