# Incoming Sprite Drop-Off

Put raw downloaded sprite sheets here (any layout — the cutter handles grid
inference and pixel-stable alignment). This directory is a **quarantine**, not
the corpus: nothing here is training data until it clears intake.

## How to deliver from your PC

1. From your machine, in a clone of this repo:
   `git checkout claude/project-comprehensive-review-77z4yi`
   copy your sheets into `am-pixel/data/incoming/`, then commit and push.
2. Or attach files directly in the Claude session chat (fine for a handful;
   use git for bulk).

## REQUIRED: provenance sidecar (Constitution Rule 5)

For every sheet, add a line to `SOURCES.csv` in this directory:

```csv
filename,source_url,creator,license,license_url,notes
knight_sheet.png,https://opengameart.org/content/...,AuthorName,CC0,https://creativecommons.org/publicdomain/zero/1.0/,walk+idle rows
```

Accepted licenses: **CC0, CC-BY** (attribution recorded), commissioned
work-for-hire. **CC-BY-SA is on legal hold (CHANGE-038). Unknown license =
cannot enter training** — the pipeline will refuse it at the provenance gate.
Sheets with unknown/none licensing may still be used to TEST the cutter, but
they stay quarantined here and never receive a manifest entry.

## Intake pipeline (run per sheet or batch)

```bash
cd am-pixel
# 1. cut with pixel-stable alignment (review the *_ghost.png overlays!)
PYTHONPATH=. python3 data/pipeline/sheet_cutter.py data/incoming/SHEET.png data/incoming/cut/SHEET/
# 2. after provenance entries are written, index into the corpus
PYTHONPATH=. python3 data/pipeline/indexer.py data/incoming/cut/SHEET/frame.png data/corpus/train/ID.npz
```

The cutter writes, per animation row: aligned frames, a `_ghost.png` overlay
(all frames superimposed — bounce shows as edge smearing), and a JSON cut
report with per-row stability. A row flagged `stable: false` will bounce in
game — fix with `--grid`/`--align correlate-xy` or manual review before use.
