# decision_log.md

Reasoning log for **non-mechanical** decisions (CHANGE-027). Primary instrument for human and LLM drift detection.

**Mechanical trigger — an entry IS required when:**
- Choosing between two or more valid paths
- Governing instruction uses: if / may / consider / evaluate / when needed
- Deviating from a documented procedure, even slightly
- Deciding something is or is not a blocker
- Deciding a failure pattern warrants a specific intervention
- Any action with Risk Level **High** or **Irreversible**

**Mechanical execution** (running a script, commit after approval, installing a dependency, generating from a confirmed prompt) — **no** entry if fully specified by documents.

---

## Entry schema

```
## [ISO 8601 Date] | Phase [N] | [Category]

**Decision:** [One sentence]
**Governing Rule:** [Exact reference — e.g. SPEC §4.3 / CONSTITUTION Rule 5 / ROADMAP Phase 4 Gate]
**Alternatives Considered:** [What else and why rejected]
**Rationale:** [Why this choice]
**Confidence:** [Low / Medium / High]
**Risk Level:** [Low / Medium / High / Irreversible]
**Reversible:** [Yes / No — if No, recovery path]
```

**Categories:** Architecture | Quality | DataPipeline | PhaseGate | EscalationJudgment | ProcessDeviation

---

*Initialized Phase 0 — CHANGE-027.*

---

## 2026-07-01 | Phase 0 | EscalationJudgment

**Decision:** Accept the human's written session authorization ("i give you full authority to do what you feel is right… ignore that stop and do what you can moving forward") as the explicit confirmation Rule 9 requires for overriding procedural halts THIS SESSION — scoped to: proceeding past the Golden Dataset procurement stop, and running a tier-0-only validation training run before PHASE4_ARCHITECTURE_REVIEW approval.
**Governing Rule:** CONSTITUTION Rule 9 (Human Override Authority), Rule 6 (Architecture Review Gate), CHANGE-037
**Alternatives Considered:** (a) Halt at Phase 3 data gate — rejected: human explicitly pre-authorized proceeding; (b) run production-path training on synthetic data — rejected: violates the synthetic-training ban and would poison the production gate.
**Rationale:** Rule 9 requires stating the implicated rules and getting explicit confirmation; the human's message IS that confirmation, given in advance and in writing. **The driving reason for overriding procedural halts rather than waiting: the human's access to this build agent (Fable 5) is a limited window closing 2026-07-07 — waiting on asynchronous human-in-the-loop steps would forfeit irreplaceable build capacity.** The human additionally delegated human-in-the-loop authority for this window ("i've given you authority to act as myself being the human in the loop", 2026-07-01). The production gates are untouched: training_run_gate still requires human approval; the validation run used a separate gate that refuses anything but tier-0 data and writes checkpoints to a separate directory. Scope note: this delegation is exercised for procedural/process gates; it is NOT used to self-certify quality judgments the Bible reserves for human eyes (Soul/Originality scoring, Golden Dataset curation), which would defeat their purpose rather than expedite them.
**Confidence:** High
**Risk Level:** Medium
**Reversible:** Yes — validation checkpoints and Tier 0 corpus are deletable without touching production state; provenance entries are tier-0-flagged.

## 2026-07-01 | Phase 0 | Architecture

**Decision:** Implement generation as a mask-determined three-phase order (mask → outline → interior) instead of the literal four-category order.
**Governing Rule:** SPEC §3.2 (CHANGE-001/014), OPENCLAW_PROMPT Rule 9/CHANGE-020 (document deviations, human review before production training)
**Alternatives Considered:** (a) literal four-category order — ill-posed at inference (structural category depends on the finished sprite); (b) raster order — discards the spec's structure-aware intent; (c) joint (position,value) prediction — significantly more complex, not justified before the Phase 4 experiment.
**Rationale:** Preserves "silhouette first, outline second" exactly while keeping every token's position computable at sampling time. Full rationale and cost analysis in model/architecture/IMPLEMENTATION_NOTES.md §3.
**Confidence:** High
**Risk Level:** High (architecture) — mitigated by CHANGE-020 human review before any production training
**Reversible:** Yes — tokenizer-level change; corpus .npz format is order-agnostic.

## 2026-07-01 | Phase 0 | DataPipeline

**Decision:** Build and train on a Tier 0 synthetic validation corpus (CHANGE-037) because every approved data source is unreachable from this environment.
**Governing Rule:** SPEC §15, OPENCLAW_PROMPT Training Data Approach, CHANGE-037
**Alternatives Considered:** (a) skip all training — leaves the training loop unproven, wasting the authorized session; (b) fetch from GitHub mirrors of CC0 packs — outside this session's authorized repository scope.
**Rationale:** The synthetic-data ban prevents quality circularity in the production model; a clearly-flagged tier-0 smoke test does not touch production. Provenance entries are tier 0 + license synthetic-validation; production_entries() and train.py both exclude them structurally.
**Confidence:** High
**Risk Level:** Low
**Reversible:** Yes

## 2026-07-01 | Phase 0 | Quality

**Decision:** Commit a 40-pair anti-pattern sample; the full 500+ dataset is regenerated deterministically on demand (generator.py, seed 99).
**Governing Rule:** ROADMAP Phase 3 (500+ anti-pattern dataset), Git hygiene
**Alternatives Considered:** Committing 1,000+ generated PNGs — bloats history for reproducible artifacts.
**Rationale:** The generator is the artifact; its output is deterministic. Tests regenerate pairs on the fly and enforce the ≥90% detection gate.
**Confidence:** Medium
**Risk Level:** Low
**Reversible:** Yes
