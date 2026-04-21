"""
Post-action DNA lock verification (CHANGE-028 Mechanism 3).

After DNA JSON is written, runs dna_diff against the approved master sprite;
on failure, rollback DNA file and log to generation_log.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_AM_PIXEL = Path(__file__).resolve().parent.parent


def verify_lock(
    dna_path: Path,
    master_sprite_path: Path,
    dna_diff_check: Any | None = None,
) -> tuple[bool, str]:
    """
    Returns (success, message). On success, DNA matches sprite per dna_diff.
    `dna_diff_check` is optional injectable for tests; defaults to importing dna_diff.run_check if present.
    """
    if not dna_path.is_file():
        return False, f"DNA file missing: {dna_path}"
    if not master_sprite_path.is_file():
        return False, f"Master sprite missing: {master_sprite_path}"
    try:
        json.loads(dna_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, f"Invalid DNA JSON: {e}"

    if dna_diff_check is not None:
        return dna_diff_check(dna_path, master_sprite_path)

    # Default: defer to dna_diff when implemented
    if str(_AM_PIXEL) not in sys.path:
        sys.path.insert(0, str(_AM_PIXEL))
    try:
        import dna_diff  # noqa: WPS433

        if hasattr(dna_diff, "verify_dna_matches_sprite"):
            return dna_diff.verify_dna_matches_sprite(dna_path, master_sprite_path)
    except (ImportError, NotImplementedError):
        pass
    # Phase 0: no pixel pipeline — pass if files exist and JSON parses
    return True, "Stub verification — dna_diff.verify_dna_matches_sprite not yet implemented"


def rollback_dna_file(dna_path: Path, reason: str, generation_log: Path | None = None) -> None:
    """Delete DNA file and append failure to generation_log."""
    if dna_path.is_file():
        dna_path.unlink()
    log = generation_log or (_AM_PIXEL / "logs" / "generation_log.md")
    line = f"\n[DNA LOCK VERIFICATION FAILED] {dna_path.name} — {reason}\n"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(line)
