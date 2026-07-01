# Training Data Sources

Register every source with URL and license status BEFORE scraping (SPEC §15).
CC-BY-SA is ON HOLD pending legal review (CHANGE-038) — do not ingest.

## Network status — 2026-07-01 session

| Source | License policy | Status |
|--------|----------------|--------|
| opengameart.org | per-asset (accept CC0/CC-BY only) | BLOCKED — egress proxy 403 in this environment |
| itch.io free packs | per-asset (accept CC0/CC-BY only) | BLOCKED — egress proxy 403 |
| kenney.nl | CC0 | BLOCKED — egress proxy 403 |

No scraping performed this session. See logs/BLOCKERS.md. The scraper
(data/scraper/scraper.py) is implemented and tested for provenance-first
ordering; point it at these sources from a network-enabled machine.

## Legal review holds

- CC-BY-SA: awaiting written legal opinion (CHANGE-038). Record the opinion here before any ingestion.
