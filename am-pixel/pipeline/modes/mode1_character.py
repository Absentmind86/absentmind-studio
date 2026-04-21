"""
Mode 1 — Character Creation

CRITICAL RULES FOR THIS MODE:
1. Every candidate scored via rubric_scorer.py (automated gate: 85 pts) before human sees it.
   Below 85/85 automated = rebuild from silhouette. Not a patch. [CONSTITUTION Rule 4]
2. DNA lock is irreversible without rollback procedure. Call compliance.dna_lock_gate()
   before any lock. [SPEC §4.3]
3. All derived profiles generated from DNA JSON — not re-derived from sheet image.
4. Non-master profile generation uses twin input:
   [DNA] + [Complete Brief including occluded_features] + [Master View Tokens]. [CHANGE-016]
5. Every sheet frame evaluated individually against rubric AND DNA continuity.
   A sheet is not approved until all frames pass.

See SPEC §5.1, CONSTITUTION.md, tools/compliance.py. Phase 0 stub implementation.
"""

# Implementation pending — structure only.


def main() -> None:
    raise NotImplementedError("Mode 1 — Character creation")


if __name__ == "__main__":
    main()
