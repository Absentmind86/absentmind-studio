# BLOCKERS.md
# Documented blockers awaiting human input.
# A blocker is any task that cannot be resolved after 48 hours of genuine attempts.
# Format: Date | Phase | Task | What Was Attempted | Options | Status

| Date | Phase | Task | Attempted | Options | Status |
|------|-------|------|-----------|---------|--------|
| 2026-07-01 | 3 | Tier 1/2 training-data procurement | opengameart.org, itch.io, kenney.nl all return 403 at this environment's egress proxy; GitHub access scoped to this repo only. Scraper fully implemented (provenance-first, robots-aware) but cannot reach any approved source from here. | (a) Run scraper from a network-enabled machine; (b) human downloads CC0/CC-BY packs and drops them into data/corpus/ for the pipeline; (c) widen network policy for this environment. | OPEN — pipeline proven on Tier 0; real data drop-in requires no code changes |
| 2026-07-01 | 4 | Production training authorization | PHASE4_ARCHITECTURE_REVIEW: PENDING. IMPLEMENTATION_NOTES.md written and ready for human review (includes one documented deviation: mask-determined three-phase generation order, §3). | Human reviews model/architecture/IMPLEMENTATION_NOTES.md; if approved, set PHASE4_ARCHITECTURE_REVIEW: APPROVED in logs/phase_gates.md. | OPEN — awaiting human review (Constitution Rule 6) |
