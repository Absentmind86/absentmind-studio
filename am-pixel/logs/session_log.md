# session_log.md

Append-only log of **Session Start Summaries** (OPENCLAW_PROMPT Rule 11 / CHANGE-026).

One block per OpenClaw session — written **before** any tool use, file write, or code execution. Never truncated. Used to detect cross-session disorientation during review.

---

### Template (each session)

```
## [ISO 8601 datetime]

**Phase / gate:** …
**CONSTITUTION:** Confirmed Rules 1–9 in context — [yes/no]
**phase_gates.md:** Current phase … | Last gate … | Next unchecked …
**BLOCKERS:** …
**generation_log.md (last 10):** Pass-rate trend — improving / stable / degrading
**ROADMAP today:** Next task — …
**Summary (~200 words):** …
```

---

*Initialized Phase 0 — CHANGE-026.*
