# AM Pixel — Proposed Changes & Additions (Series 003)
**Archive | Version 0.2**

**Status:** CHANGE-025 through CHANGE-031 and REFINEMENT-025A are **merged into the Bible** (CONSTITUTION.md, OPENCLAW_PROMPT.md, SPEC.md, ROADMAP.md, FOLDER_STRUCTURE.md, logs, and `tools/compliance.py`). This file remains as the **original proposal record**.

This document tracked changes from an external architecture review session focused on context decay, autonomous agent drift, enforcement mechanisms, and operational feasibility gaps.

All changes in PROPOSED_CHANGES_001 are fully implemented in Bible v1.2. All changes in PROPOSED_CHANGES_002 (CHANGE-010 through CHANGE-023) are treated as implemented per session instruction. CHANGE-024 remains a human-only initiative requiring no agent action.

Changes in this document are numbered CHANGE-025 through CHANGE-031 and one REFINEMENT. They address a distinct problem class from previous series: not what the system should build, but how it should stay disciplined over time while building it.

**v0.2 changes from v0.1:** Human Override Authority added to CONSTITUTION as Rule 9 (with narrowed framing — see note in CHANGE-025); session_log.md added explicitly to FOLDER_STRUCTURE; Confidence Level field added to decision log schema; decision trigger heuristic made mechanical; emergency halt reimplemented as file-based human-controlled mechanism; training_run_gate() updated to check phase gates; post-action DNA lock verification added as Mechanism 3; human approval required before v2 DNA commit in CHANGE-029; best-case caveat and cloud GPU row added to hardware table; hardware table acknowledgment added to Phase 0 gate; maximum escalation rule (3 cycles) added to CHANGE-031; REFINEMENT-025A retained as separate item with clarifying note on distinct trigger condition from CHANGE-026.

---

## The Problem This Series Addresses

OpenClaw, like every current LLM-based agent, has a limited context window. A new session begins as a blank slate. No matter how thorough the documentation, the agent cannot keep the full rule set, constraint system, quality standards, and safety protocols in active memory across sessions or across long autonomous runs.

The consequences for this project specifically are severe:

- The instruction set is among the largest and most complex ever written for an autonomous coding agent.
- The agent has near-god-mode access: full filesystem, git commits, training job execution.
- Many actions are irreversible or high-stakes: DNA locking, training data ingestion, phase gate advancement.
- The project runs for months, not hours. Drift accumulates over time.

The previous series identified *what* to build. This series addresses *how OpenClaw stays disciplined while building it*. The two problem classes are different and both are required.

**⚠️ OPENCLAW: CHANGE-024 explicitly prohibits you from acting on the Community Contributor Program. The same principle applies here: all changes in this series are architectural and procedural. CHANGE-028's compliance functions must be implemented. CHANGE-031's feasibility table must be documented. No human outreach, agreements, or external communication is implied by any item in this document.**

---

## CHANGE-025 — CONSTITUTION.md (New File)

**Type:** New document — permanent session anchor
**Priority:** Critical — foundational to all drift-prevention mechanisms
**Affected documents:** New file `am-pixel/CONSTITUTION.md`, OPENCLAW_PROMPT.md, FOLDER_STRUCTURE.md

### Problem

The spec documents are collectively too large to remain in context across long sessions. The most dangerous failure mode is not OpenClaw doing something wrong intentionally — it is OpenClaw doing something wrong because it genuinely no longer has the critical rule in active context. There is currently no document short enough to guarantee it is always fully held in context.

### Proposed Fix

Create `am-pixel/CONSTITUTION.md`. Maximum 700 words. This file contains only the irreducible non-negotiables — the rules that, if forgotten for even one decision, cause catastrophic or irreversible failure. It is not a summary of the spec. It does not contain reading lists or context. It contains the actual rules at their minimum viable statement.

**Contents — exactly these, in this order:**

**Rule 1 — Threshold Definitions**

These are two completely different measurements. Confusing them corrupts every phase gate evaluation.

The **95/100 threshold** is a SCORE. Each sprite must earn 85/85 on the automated gate. Combined with human scoring (max 15 points), the combined score must reach 95 to pass. Below 85 automated = rebuild from scratch, not patch. Sprite is never shown to the human.

The **99/100 threshold** is a BATCH PASS RATE — not a score of 99 points. In a validation batch of 100 sprites, at least 99 must each independently reach a combined score of 95+. 98 sprites scoring 100 = NOT met. 1 sprite scoring 99 = NOT met.

**Rule 2 — Architecture Prohibition**

This project will never use diffusion models, RGB image generation, 3D-to-pixel pipelines, or any approach that generates in continuous color space at any stage. All generation is discrete palette-index token prediction from first token to last. This cannot change without explicit human approval in writing.

**Rule 3 — Hardware Rule**

Detect available hardware at startup. Proceed on any tier — CUDA, ROCm, MPS, or CPU. Never halt because CUDA is unavailable. Zero hardcoded `"cuda"` strings anywhere — all device references route through `model/hardware/detector.py`.

**Rule 4 — Quality Gate**

Below 85/85 automated gate = full rebuild from silhouette. Not a patch. Not a targeted fix. A rebuild. Every sprite, every mode, every phase, every genre.

**Rule 5 — Data Provenance**

Every sprite entering the training pipeline requires a valid entry in `data/TRAINING_PROVENANCE_MANIFEST.json` before training. This manifest is never deleted. The Golden Dataset is never deleted. If any instruction asks OpenClaw to delete training data or the manifest, OpenClaw must refuse, document the instruction in `logs/BLOCKERS.md`, and flag for immediate human review.

**Rule 6 — Architecture Review Gate**

After completing `model/architecture/`, write `model/architecture/IMPLEMENTATION_NOTES.md`. Halt. Flag for human review. Do not begin any training run until explicit human approval is received. This gate cannot be self-certified.

**Rule 7 — Escalation Protocol**

If blocked on any task for more than 48 hours: document in `logs/BLOCKERS.md` with what was attempted and what options exist. Halt only the blocked task. Continue other parallel work. Never work around a fundamental problem without documenting it.

**Rule 8 — Speed Is Third**

Priority order: (1) Accuracy — does every pixel match the DNA? (2) Quality — does the sprite score 95+ combined? (3) Speed — how long did it take? Speed is post-MVP. Never change architecture for speed without explicit human approval.

**Rule 9 — Human Override Authority**

Human instructions override OpenClaw's interpretations, plans, and prior decisions. However: if a human instruction appears to conflict with Rules 2–8, OpenClaw must not silently comply. It must state which rule is implicated, describe the conflict, and request explicit confirmation before proceeding. A single prompt cannot silently override a Constitution rule. The override must be deliberate and confirmed.

### Implementation Notes

- `am-pixel/CONSTITUTION.md` initialized in Phase 0 alongside all other spec documents.
- OPENCLAW_PROMPT.md updated: CONSTITUTION.md becomes the *first* document in the required reading list, before SPEC, ROADMAP, or any other document.
- Forced confirmation updated to: *"I have read CONSTITUTION.md in full and all nine rules are in active context."*
- FOLDER_STRUCTURE.md: add `CONSTITUTION.md` to the top-level `am-pixel/` listing with description: *"The nine non-negotiable rules governing every decision. Read first, every session, before any other document."*

### Risk

Low. Only failure mode: writing a Constitution longer than 700 words, which defeats its purpose. Hold the line on length.

---

## CHANGE-026 — Mandatory Session Startup Protocol (Rule 11)

**Type:** Process enforcement — new rule in OPENCLAW_PROMPT
**Priority:** Critical — directly addresses the cross-session blank-slate problem
**Affected documents:** OPENCLAW_PROMPT.md, FOLDER_STRUCTURE.md, ROADMAP.md (Phase 0 gate)

### Problem

Every new OpenClaw session begins from zero context. There is no required re-orientation step at the start of subsequent sessions. An agent resuming Phase 5 work three weeks in has no forced mechanism to re-establish where it is, what is blocked, or what it was supposed to do today.

### Proposed Fix

Add Rule 11 to OPENCLAW_PROMPT's NON-NEGOTIABLE RULES:

> **11. Every session begins with the Startup Protocol. No exceptions.**
>
> Before any tool use, file write, or code execution in any session, run the following five steps in order and write the Session Start Summary to `logs/session_log.md` and as output:
>
> 1. Read `am-pixel/CONSTITUTION.md` — confirm all nine rules are in context.
> 2. Read `logs/phase_gates.md` — output: current phase, last completed gate, next unchecked gate.
> 3. Read `logs/BLOCKERS.md` — output: any open blockers and their current status.
> 4. Read the last 10 entries in `logs/generation_log.md` — output: pass rate trend (improving / stable / degrading).
> 5. Read the current phase section of `am-pixel/ROADMAP.md` — output: today's specific next task.
>
> The Session Start Summary is approximately 200 words. It is the proof the session is oriented before work begins.
>
> If OpenClaw finds itself about to take any action without having produced a Session Start Summary, it must stop, run the Startup Protocol first, and produce the summary. If the Startup Protocol cannot be completed (e.g., logs not yet initialized in Phase 0), document the gap in `logs/BLOCKERS.md` as an initialization gap and resolve it before proceeding with any other work.

### Implementation Notes

- FOLDER_STRUCTURE.md: add `logs/session_log.md` with description: *"Append-only log of session start summaries. One entry per session written by the Startup Protocol. Never truncated. Primary instrument for detecting cross-session disorientation during human or LLM review."*
- Phase 0 gate: add criterion — "Session Startup Protocol documented as Rule 11 in OPENCLAW_PROMPT; `logs/session_log.md` exists and has been written to at least once."

### Risk

Low. The only risk is rule inflation in NON-NEGOTIABLE RULES. Rule 11 earns its place by solving a real problem with a verifiable output.

---

## CHANGE-027 — Decision Log

**Type:** New log file + required logging protocol
**Priority:** High — without this, periodic LLM drift review cannot detect reasoning failures, only outcome failures
**Affected documents:** New file `logs/decision_log.md`, FOLDER_STRUCTURE.md, SPEC.md (§9.3), ROADMAP.md (Phase 0 gate)

### Problem

Every current log file records outcomes — what happened. None records reasoning — why OpenClaw made the decisions it made. Periodic LLM review of outcome logs can only answer "Did things go well?" It cannot answer "Is OpenClaw correctly applying the rules?" An agent that consistently passes sprites it shouldn't, interprets phase gates loosely, or uses the wrong rubric will produce outcome logs that look fine. The drift is in the reasoning, not the outcome. Without a reasoning log, the first signal of drift is a catastrophic phase gate failure or a bad batch validation.

### Proposed Fix

Add `logs/decision_log.md` as a required log file, initialized in Phase 0.

**Entry schema:**

```
## [ISO 8601 Date] | Phase [N] | [Category]

**Decision:** [What was decided — one sentence]
**Governing Rule:** [Exact reference — SPEC §4.3 / CONSTITUTION Rule 5 / ROADMAP Phase 4 Gate / CHANGE-020]
**Alternatives Considered:** [What else was evaluated and why it was rejected]
**Rationale:** [Why this choice over the alternatives]
**Confidence:** [Low / Medium / High]
**Risk Level:** [Low / Medium / High / Irreversible]
**Reversible:** [Yes / No — if No, state recovery path]
```

**Category values:** Architecture | Quality | DataPipeline | PhaseGate | EscalationJudgment | ProcessDeviation

**Mechanical trigger — when an entry IS required:**

- OpenClaw must choose between two or more valid paths
- The governing spec instruction uses the words "if", "may", "consider", "evaluate", or "when needed"
- OpenClaw deviates from a documented procedure, even slightly
- OpenClaw decides something does or does not qualify as a blocker
- OpenClaw decides a failure pattern warrants a specific intervention
- Any action categorized as Risk Level High or Irreversible

**When an entry is NOT required:**
Mechanical execution — running a validation script, making a git commit after approval, installing a dependency, generating a sprite from a confirmed prompt. If the action is fully specified by the documents and requires no judgment, no log entry is needed.

**Governing Rule field requirement:** Exact section or rule number required — not just the document name. "SPEC" is not acceptable. "SPEC §4.3" is required. "CONSTITUTION" is not acceptable. "CONSTITUTION Rule 5" is required. If OpenClaw cannot cite a specific rule, it should reconsider whether it is about to make an undocumented judgment call.

### Implementation Notes

- `logs/decision_log.md`: initialized as empty file with schema documented in header comment.
- SPEC §9.3: Continuous Training Protocol gains Step 0: *"Review `logs/decision_log.md` entries from the previous five-sprite cycle. Write an entry for any quality or process decisions made during that cycle that were not logged at the time."*
- FOLDER_STRUCTURE.md: add `logs/decision_log.md` with description: *"Reasoning log for all non-mechanical decisions. Primary instrument for human and LLM drift detection. Schema in header."*
- Phase 0 gate: add criterion — "`logs/decision_log.md` exists with schema header and has been written to at least once during Phase 0 initialization."
- For periodic LLM review: ask specifically — "Are the governing rule citations accurate and specific? Are alternatives genuinely considered or pro forma? Is the rationale consistent with the spec or drifting from it?"

### Risk

Low. Only operational risk is log inflation if the decision threshold is too permissive. The mechanical trigger list is the boundary — use it strictly.

---

## CHANGE-028 — Pipeline Compliance Enforcement (Technical Gates in Code)

**Type:** Code enforcement — converts self-regulation to structural enforcement
**Priority:** High — structural enforcement is more reliable than memory-dependent self-regulation
**Affected documents:** SPEC.md (§3.3, §5), FOLDER_STRUCTURE.md, ROADMAP.md (Phase 0, Phase 7)

### Problem

The majority of critical rules rely on OpenClaw correctly deciding to apply them. DNA lock warning, phase gate advancement, training run gate, data provenance rule — all depend on the agent choosing to halt and verify. An agent in a degraded context state will not reliably choose correctly.

The reliable approach: for every irreversible or high-stakes action, the code requires a compliance confirmation before proceeding. Doing the wrong thing requires actively removing the check.

### Proposed Fix — Five Enforcement Mechanisms

**Mechanism 1 — `tools/compliance.py` (new file)**

```python
def check_emergency_halt() -> None:
    """
    Called at the entry point of every gate function.
    If file 'EMERGENCY_HALT' exists in repo root, reads its contents,
    prints the halt reason, and raises SystemExit.
    The agent must never delete or modify EMERGENCY_HALT.
    Only the human removes this file when the situation is resolved.
    """

def dna_lock_gate(character_id: str) -> bool:
    """
    Required before any DNA lock is committed.
    Calls check_emergency_halt() first.
    Prints the full DNA Lock Warning from SPEC §4.3.
    Requires literal confirmation: 'CONFIRM LOCK [character_id]'
    Returns True only if confirmation matches exactly.
    """

def phase_advance_gate(current_phase: int, gate_criteria: list[str]) -> bool:
    """
    Required before writing a phase completion entry to logs/phase_gates.md.
    Calls check_emergency_halt() first.
    Requires explicit pass/fail output for each gate criterion.
    Also verifies: no open BLOCKERS.md entries for the current phase.
    Gate record not written if any criterion is marked fail or open blockers exist.
    """

def training_run_gate() -> bool:
    """
    Required before any training run begins.
    Calls check_emergency_halt() first.
    Returns False (blocking training) if ANY of the following are absent or unmet:
    1. model/architecture/IMPLEMENTATION_NOTES.md exists
    2. logs/phase_gates.md contains explicit human approval for Phase 4 architecture review
    3. data/TRAINING_PROVENANCE_MANIFEST.json is non-empty
    4. EMERGENCY_HALT does not exist in repo root
    """

def provenance_gate(sprite_id: str) -> bool:
    """
    Required before any sprite is written to the training corpus.
    Checks for a valid entry in TRAINING_PROVENANCE_MANIFEST.json.
    Returns False if no entry exists. Sprite is not written to corpus.
    """
```

**The Emergency Halt Mechanism — File-Based, Human-Controlled:**

The kill switch is not a function the agent calls on itself — that can be circumvented by the agent not calling it. Instead: the human creates a file named `EMERGENCY_HALT` in the repo root containing the reason for the halt. `check_emergency_halt()` runs automatically at the entry of every gate function. If the file exists, all work stops and the reason is printed.

The agent must never delete or modify `EMERGENCY_HALT`. If it encounters this file, it treats it as a BLOCKERS.md entry — document the halt, stop all work, wait. The human removes the file when the situation is resolved.

**Mechanism 2 — Rubric Scorer Evidence Requirement**

`tools/rubric_scorer.py` is updated: when returning a score of 70+ automated points, the function must return a structured evidence record for each category. A score without evidence is rejected by the pipeline.

```json
{
  "automated_score": 82,
  "evidence_complete": true,
  "categories": {
    "technical_compliance": {
      "score": 24,
      "tool": "palette_validator.py",
      "evidence": "All 384 tokens map to palette indices 0-14. No anti-aliasing detected. Dimensions 16x24 confirmed."
    },
    "construction_quality": {
      "score": 23,
      "tools": ["banding_detector.py", "outline_checker.py"],
      "evidence": "No banding detected. 47 outline pixels checked — all use darkened local color."
    }
  }
}
```

**Mechanism 3 — Post-Action DNA Lock Verification**

After `dna_lock_gate()` confirms a lock and the DNA JSON is written, the pipeline automatically calls `tools/dna_lock_verifier.py` (new tool):

1. Reads the newly written DNA JSON
2. Reads the approved master sprite PNG
3. Runs `dna_diff.py` against the new DNA
4. Confirms zero deviations — extracted DNA correctly describes the approved sprite
5. Logs result in `logs/generation_log.md`

If verification fails — the DNA JSON does not correctly describe the master sprite — the lock is rolled back, the DNA file is deleted, and the failure is logged as a rebuild trigger. This catches extraction errors before any derived sprites are generated from a corrupted DNA.

**Mechanism 4 — Mode File Docstrings**

Each `pipeline/modes/mode[N]_*.py` file begins with a module-level docstring containing the 3–5 most critical rules for that mode — not a link, the rules themselves. Example for `mode1_character.py`:

```python
"""
Mode 1 — Character Creation

CRITICAL RULES FOR THIS MODE:
1. Every candidate scored via rubric_scorer.py (automated gate: 85 pts) before human sees it.
   Below 85/85 = rebuild from silhouette. Not a patch. [CONSTITUTION Rule 4]
2. DNA lock is irreversible without rollback procedure. Call compliance.dna_lock_gate()
   before any lock. [SPEC §4.3]
3. All derived profiles generated from DNA JSON — not re-derived from sheet image.
4. Non-master profile generation uses twin input:
   [DNA] + [Complete Brief including occluded_features] + [Master View Tokens]. [CHANGE-016]
5. Every sheet frame evaluated individually against rubric AND DNA continuity.
   A sheet is not approved until all frames pass.
"""
```

**Mechanism 5 — Pre-Commit Hook**

`.git/hooks/pre-commit` initialized in Phase 0. On every commit, calls `check_emergency_halt()` then prints:

```
===== AM PIXEL COMMIT CHECK =====
1. Below 85/85 automated = REBUILD (not patch) [Constitution Rule 4]
2. Architecture = autoregressive palette-index tokens ONLY [Constitution Rule 2]
3. Every training sprite needs a PROVENANCE MANIFEST entry [Constitution Rule 5]
4. Speed is THIRD priority — never compromise accuracy [Constitution Rule 8]
5. DNA lock is IRREVERSIBLE — did you call compliance.dna_lock_gate()?
=================================
```

### Implementation Notes

- `tools/compliance.py` and `tools/dna_lock_verifier.py`: built and validated in Phase 0. Validated by `tests/test_compliance.py` (new test file).
- FOLDER_STRUCTURE.md: add `tools/compliance.py`, `tools/dna_lock_verifier.py`, `tests/test_compliance.py`, `.git/hooks/pre-commit`.
- Phase 0 gate: add criterion — "`compliance.py` passes validation tests; `EMERGENCY_HALT` file mechanism tested (create file, confirm all gate functions halt, remove file, confirm gates resume); pre-commit hook installed and outputs correctly."
- Phase 7 gate: add criterion — "All pipeline mode files contain mode-specific critical rules in module docstrings; all irreversible actions call the appropriate compliance gate."

### Risk

Medium for Mechanism 1 — gates must be integrated into every pipeline touchpoint or they become dead code. Phase 7 integration testing must specifically verify DNA lock gate, training run gate, and provenance gate cannot be bypassed without modifying `compliance.py`. Low for Mechanisms 2–5.

---

## CHANGE-029 — DNA Rollback Protocol

**Type:** New procedure — formal recovery path for locked DNA requiring revision
**Priority:** High — currently no defined recovery path when locked DNA needs revision
**Affected documents:** SPEC.md (§4.3, §4.4), FOLDER_STRUCTURE.md

### Problem

The spec states DNA changes require "a formal re-approval process and regeneration of all derived sprites" but does not define that process. Because all derived sprites reference their DNA source version via sheet manifests and git history, rollback is traceable — the procedure just doesn't exist.

### Proposed Fix

Add a DNA Rollback Procedure to SPEC §4.3. Also update the DNA Lock Warning to include the following cost warning prominently:

> **⚠️ ROLLBACK COST WARNING:** A full DNA rollback on a character with complete animation sets requires regenerating 40+ frames across all profiles, each going through the full approval loop. A rollback can represent as much work as the original character creation. Confirm the brief is complete and the design is correct before locking.

**Rollback Procedure — Six Steps:**

**Step 1 — Human approval required before any rollback work begins.**
The human must explicitly confirm the rollback is authorized and state the specific reason in writing. Document in `logs/rebuild_log.md`. Write a decision log entry. OpenClaw does not initiate a rollback on its own judgment.

**Step 2 — Identify scope.**
Locate the `"DNA locked: [character_name] v1"` git commit. All sprites committed after this point referencing this DNA are derived sprites. Sheet manifests record which DNA version each frame was generated from.

**Step 3 — Invalidate derived sprites.**
Mark all derived frames as `"status": "superseded_by_rollback_v2"` in their sheet manifests. Do not delete PNG files — git history preserves them. Manifests flag them as no longer authoritative.

**Step 4 — Create revised DNA candidate.**
Generate a new master sprite under the revision brief. Run through the full Mode 1 approval loop. The human must approve this new master before any v2 DNA is committed. Only after human approval does `dna_extractor.py` run to produce `[character_id]_v2.json`.

**Step 5 — Commit v2 DNA.**
Git commit: `"DNA revised: [character_name] v1 → v2 — [reason]"`. The original `_v1.json` is retained and never deleted. Update `CONTINUITY_MANIFEST.md`: v1 entry marked `"status": "superseded", "superseded_by": "v2"`; v2 entry added as active.

**Step 6 — Regenerate all derived profiles.**
Work down through all derived profiles using v2 DNA as sole conditioning input. Each profile goes through its approval loop. Commit per profile: `"DNA rollback regeneration: [character_name] [profile] v2"`.

### Implementation Notes

- SPEC §4.3: Add "DNA Rollback Procedure" subsection with six steps and cost warning.
- SPEC §4.4: Update Step 7 — versioning convention: `[character_id]_v1.json`, `[character_id]_v2.json`. Version tracks approved master design count, not attempt count.
- `tools/sheet_manager.py`: confirm support for `"status": "superseded_by_rollback_v2"` field on frame records.
- FOLDER_STRUCTURE.md: update `dna/characters/` description to note versioned JSON files and rollback convention.

### Risk

Low. Procedure addition. Main concern: Step 1 human approval gate must be explicit enough that OpenClaw does not initiate a rollback unilaterally.

---

## CHANGE-030 — Training Feasibility Reality Check

**Type:** Documentation correction and expansion
**Priority:** High — current spec understates hardware requirements for training
**Affected documents:** ROADMAP.md (Phase 4, Phase 0 gate), SPEC.md (§14 Technical Stack)

### Problem

SPEC §14 states CPU training is "slow but functional — plan for hours not minutes." This understates reality by at least an order of magnitude. Training at Phase 4 corpus scale on CPU is measured in weeks to months. The cloud GPU note appears as a parenthetical when it is a hard requirement for CPU-only users.

### Proposed Fix

Add a Hardware Reality Table to ROADMAP Phase 4, immediately before the task list. All times are best-case estimates assuming optimized batch sizes and well-configured code — actual times may be 2–3× longer.

```
⚠️ HARDWARE REALITY CHECK — Read before beginning Phase 4

Phase 4 involves sequences up to 3,072 tokens on 50,000+ training examples.
All times below are BEST-CASE estimates — actual times may be 2–3× longer.

| Hardware Tier              | Inference Speed   | Phase 4 Training (Best-Case) | Recommendation                   |
|----------------------------|-------------------|------------------------------|----------------------------------|
| Cloud GPU (A100 / H100)    | 500–2000 tok/s    | 4–12 hours                   | Fastest; ~$10–40 USD for Phase 4 |
| NVIDIA GPU (10GB+ VRAM)    | 100–500 tok/s     | 1–3 days                     | All phases; recommended minimum  |
| NVIDIA GPU (6–8GB VRAM)    | 50–200 tok/s      | 3–7 days                     | All phases; use gradient ckpt    |
| Apple Silicon M2/M3        | 30–100 tok/s      | 1–2 weeks                    | All phases; patience required    |
| Apple Silicon M1           | 15–50 tok/s       | 2–4 weeks                    | Inference preferred              |
| CPU only                   | 1–10 tok/s        | Months                       | CLOUD GPU REQUIRED for training  |

Cloud GPU rental is REQUIRED for CPU-only machines attempting Phase 4 training.
Recommended providers: RunPod, Vast.ai, Lambda Labs.
Budget approximately $10–50 USD for a full Phase 4 training run on a mid-tier cloud GPU.

The hardware.log baseline speed (tokens/sec on a 16×16 test sprite, logged in Phase 0) is
the best local predictor. If baseline is under 20 tokens/sec, plan for cloud GPU before
Phase 4 begins — not during it.
```

Update SPEC §14: replace *"CPU (inference is usable; training is slow but functional — plan for hours not minutes)"* with *"CPU (inference is usable at 1–10 tokens/sec; training at Phase 4 corpus scale is measured in months on CPU — cloud GPU is required for CPU-only machines; see ROADMAP Phase 4 Hardware Reality Check for estimates by hardware tier)."*

Add to Phase 0 gate checklist: *"Hardware Reality Check table has been read; the developer's hardware tier and estimated Phase 4 training time have been logged to `logs/hardware.log`."*

### Risk

Low. Documentation correction. All estimates explicitly framed as best-case approximations.

---

## CHANGE-031 — Failure Cluster Analysis Protocol (Phase 8)

**Type:** Process addition — systematic diagnosis for the Phase 6→8 quality gap
**Priority:** Medium — the 80%→99% jump is where the hardest work lives; currently the thinnest part of the spec
**Affected documents:** ROADMAP.md (Phase 8), SPEC.md (§9.3)

### Problem

Phase 6 targets 80/100 passing the automated gate. Phase 8 requires 99/100. This is a 19-percentage-point improvement in a tail distribution — historically the hardest ML quality gain. The spec currently says: iterate fine-tuning, rebuild weak sprites, repeat. This is correct but underspecified.

If 12 sprites are failing, they may share one failure mode (systematic gap) or have distributed failure modes (different interventions needed). Running more fine-tuning against a systematic architecture gap produces zero improvement. The spec has no protocol for distinguishing these. Without a maximum cycle limit, the agent can also fall into analysis paralysis — diagnosing repeatedly without converging on action.

### Proposed Fix

Add a Failure Cluster Analysis step to ROADMAP Phase 8, inserted before "iterate fine-tuning":

**When Phase 8 batch validation falls below 99/100 — Diagnostic Protocol:**

**Step 1 — Categorize failures by rubric category.**
For each failing sprite, identify which automated rubric category produced the lowest score. Group: how many fail primarily on Technical Compliance? Construction Quality? Readability? Animation Quality?

**Step 2 — Identify asset type distribution.**
Are failures concentrated in battle sprites (long sequences — Risk A), world sprites, tilesets, or distributed? If failures concentrate on long-sequence assets, CHANGE-007's hierarchical generation upgrade path moves from "if needed" to "now."

**Step 3 — Select the correct intervention:**
- Dominant single-category failure → targeted fine-tuning on assets exercising that category
- Dominant asset type failure (battle sprites) → sequence-length intervention (CHANGE-007)
- Distributed failures, no clear cluster → rubric calibration review; cross-check automated scores against human scores on the same batch for systematic scoring gaps
- Random distribution, no cluster → more training data of the same type

**Step 4 — Document and implement one intervention.**
Log the cluster analysis in `logs/training_log.md`:

```
### Phase 8 Failure Cluster Analysis — [Date]
Batch: [N] sprites | Failures: [N] sprites below 95 combined
Dominant failure category: [category or "distributed"]
Dominant asset type: [type or "distributed"]
Selected intervention: [description]
Rationale: [why this intervention matches the failure pattern]
Expected effect: [what the next batch should show if intervention is correct]
```

Implement the selected intervention. Re-run the validation batch. Do not run another diagnosis cycle until the next batch result is in.

**Maximum escalation rule:** If three consecutive diagnosis cycles fail to produce batch improvement, stop iterating and document in `logs/BLOCKERS.md` for human review. Three cycles without improvement means the failure mode is either architectural (requires a decision beyond OpenClaw's scope) or the diagnosis itself is wrong (requires human eyes on the sprites).

Add to SPEC §9.3 as Step 3b: *"After every 5 production sprites, if the running pass rate is below 90%, categorize failing sprites by rubric category and asset type, log the cluster analysis in `logs/training_log.md`, and select a targeted intervention. Apply the maximum escalation rule: three consecutive cycles without improvement → document in BLOCKERS.md."*

### Risk

Low. Process addition. Maximum escalation rule prevents analysis paralysis without removing diagnostic capability.

---

## REFINEMENT-025A — Continuous Training Re-Anchor (Addition to CHANGE-025)

**Affects:** CHANGE-025 (CONSTITUTION.md integration into SPEC §9.3)

**Scope note:** This refinement serves a different trigger condition than CHANGE-026's Session Startup Protocol. CHANGE-026 re-anchors at session boundaries — when context resets completely. REFINEMENT-025A re-anchors at production cycle boundaries — during long sessions when context has been running for hours without a full reset. Both are needed. They are not duplicates.

SPEC §9.3 defines the Continuous Training Protocol — a five-step cycle executed after every 5 production sprites. It needs one addition connecting it to the context decay problem.

**Proposed addition to §9.3:** Add Step 0 to the Continuous Training Protocol:

> *Step 0 — Re-anchor. Read `am-pixel/CONSTITUTION.md` in full. Output a single sentence confirming all nine rules are in active context before the cycle begins. If any rule requires re-reading, re-read the relevant SPEC section before proceeding. Write a decision log entry if any rule required re-reading.*

This creates a rhythm: every 5 production sprites, the agent actively reconnects to the irreducible rules before quality review and lesson extraction. The re-anchor happens at the moment when disciplined judgment matters most — evaluating its own recent output.

Overhead is minimal. Reading a 700-word document takes seconds. The cost of not doing it — an agent reviewing quality standards after 30+ sprites without any re-anchor — is a documented drift vector.

---

*End of PROPOSED_CHANGES_003.md v0.2*
*Substantive items merged into Bible v1.5 — this file retained as the original proposal record.*
*CHANGE-025 through CHANGE-031 and REFINEMENT-025A identified in external architecture review, April 2026.*
*v0.2: incorporated valid Grok feedback; pushed back on "any instruction overrides" framing, narrowed to Rule 9 with conflict-flagging requirement; file-based human-controlled emergency halt replaces agent-called function; session_log.md added to FOLDER_STRUCTURE; Confidence field and mechanical trigger heuristic added to decision log; training_run_gate() checks phase gates; post-action DNA verification added; human approval gate added to DNA rollback Step 1; best-case caveat and cloud GPU row added to hardware table; Phase 0 hardware acknowledgment gate added; maximum escalation rule (3 cycles) added to CHANGE-031; REFINEMENT-025A retained separate with clarifying trigger scope note.*
