"""
Scraper — writes provenance manifest entry before each sprite file.

Default (no flag): writes to TRAINING_PROVENANCE_MANIFEST.json and data/corpus/.
--transformative flag (CHANGE-T04, transformative branch only): writes to
  TRAINING_PROVENANCE_MANIFEST.transformative.json and data/corpus_transformative/.
  License allowlist is suspended in this mode; scraping-block rules still apply.

See am-pixel/SPEC.md, FOLDER_STRUCTURE.md, and PROPOSED_CHANGES_004.md. Phase 0 stub.
"""
# Implementation pending — structure only.


def main() -> None:
    raise NotImplementedError("Scraper — writes provenance manifest entry before each sprite file")


if __name__ == "__main__":
    main()
