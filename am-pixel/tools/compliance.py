"""
Pipeline compliance gates (CHANGE-028). Structural enforcement — not optional memory checks.

Repo root = parent of `am-pixel/` (directory containing `am-pixel/tools/compliance.py`).
Emergency halt file: `<repo_root>/EMERGENCY_HALT` (human-created; never delete as agent).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Repo root: absentmind-studio/ (parent of am-pixel/)
_AM_PIXEL = Path(__file__).resolve().parent.parent
REPO_ROOT = _AM_PIXEL.parent


def _emergency_halt_path() -> Path:
    return REPO_ROOT / "EMERGENCY_HALT"


def check_emergency_halt() -> None:
    """
    Call at the entry point of every gate function.
    If `EMERGENCY_HALT` exists in repo root, print its contents and exit.
    The agent must never delete or modify EMERGENCY_HALT; only the human removes it.
    """
    path = _emergency_halt_path()
    if path.is_file():
        reason = path.read_text(encoding="utf-8", errors="replace")
        print("===== EMERGENCY HALT =====", file=sys.stderr)
        print(reason, file=sys.stderr)
        print("==========================", file=sys.stderr)
        raise SystemExit(2)


def dna_lock_gate(character_id: str, confirmation: str) -> bool:
    """Require literal 'CONFIRM LOCK {character_id}' before DNA lock is committed."""
    check_emergency_halt()
    expected = f"CONFIRM LOCK {character_id}"
    return confirmation.strip() == expected


def phase_advance_gate(
    current_phase: int,
    gate_criteria: list[tuple[str, bool]],
    *,
    has_open_blockers: bool = False,
) -> bool:
    """
    Before writing a phase completion entry to logs/phase_gates.md.
    Each criterion is (description, passed).
    Fails if any criterion is False or `has_open_blockers` is True.
    """
    check_emergency_halt()
    if has_open_blockers:
        return False
    for _desc, ok in gate_criteria:
        if not ok:
            return False
    return True


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def training_run_gate(
    repo_root: Path | None = None,
    manifest_path: Path | None = None,
    phase_gates_path: Path | None = None,
    implementation_notes_path: Path | None = None,
) -> bool:
    """
    Required before any training run begins.
    Returns False if any requirement is unmet.
    """
    check_emergency_halt()
    root = repo_root or REPO_ROOT
    impl = implementation_notes_path or (_AM_PIXEL / "model" / "architecture" / "IMPLEMENTATION_NOTES.md")
    if not impl.is_file():
        return False
    pg = _read_text(phase_gates_path or (_AM_PIXEL / "logs" / "phase_gates.md"))
    if "PHASE4_ARCHITECTURE_REVIEW: APPROVED" not in pg:
        return False
    manifest = manifest_path or (_AM_PIXEL / "data" / "TRAINING_PROVENANCE_MANIFEST.json")
    if not manifest.is_file():
        return False
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if not isinstance(data, list) or len(data) == 0:
        return False
    if _emergency_halt_path().is_file():
        return False
    return True


def provenance_gate(sprite_id: str, manifest_path: Path | None = None) -> bool:
    """Before writing a sprite to the training corpus — manifest must contain sprite_id."""
    check_emergency_halt()
    manifest = manifest_path or (_AM_PIXEL / "data" / "TRAINING_PROVENANCE_MANIFEST.json")
    if not manifest.is_file():
        return False
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if not isinstance(data, list):
        return False
    for entry in data:
        if isinstance(entry, dict) and entry.get("sprite_id") == sprite_id:
            return True
    return False


_TRANSFORMATIVE_MANIFEST = _AM_PIXEL / "data" / "TRAINING_PROVENANCE_MANIFEST.transformative.json"


def transformative_provenance_gate(sprite_id: str, manifest_path: Path | None = None) -> bool:
    """
    TRANSFORMATIVE BRANCH ONLY (CHANGE-T04).
    Same contract as provenance_gate() but defaults to the transformative manifest.
    Do not call this function from main-branch code.
    """
    check_emergency_halt()
    manifest = manifest_path or _TRANSFORMATIVE_MANIFEST
    if not manifest.is_file():
        return False
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if not isinstance(data, list):
        return False
    for entry in data:
        if isinstance(entry, dict) and entry.get("sprite_id") == sprite_id:
            return True
    return False


def training_run_gate_transformative(
    repo_root: Path | None = None,
    manifest_path: Path | None = None,
    phase_gates_path: Path | None = None,
    implementation_notes_path: Path | None = None,
) -> bool:
    """
    TRANSFORMATIVE BRANCH ONLY (CHANGE-T04).
    Same contract as training_run_gate() but reads from the transformative manifest.
    Architecture review gate (PHASE4_ARCHITECTURE_REVIEW: APPROVED) is preserved —
    architecture discipline is independent of data policy.
    Do not call this function from main-branch code.
    """
    check_emergency_halt()
    impl = implementation_notes_path or (_AM_PIXEL / "model" / "architecture" / "IMPLEMENTATION_NOTES.md")
    if not impl.is_file():
        return False
    pg = _read_text(phase_gates_path or (_AM_PIXEL / "logs" / "phase_gates.md"))
    if "PHASE4_ARCHITECTURE_REVIEW: APPROVED" not in pg:
        return False
    manifest = manifest_path or _TRANSFORMATIVE_MANIFEST
    if not manifest.is_file():
        return False
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if not isinstance(data, list) or len(data) == 0:
        return False
    if _emergency_halt_path().is_file():
        return False
    return True


def print_pre_commit_banner() -> None:
    """Reminder lines — run after check_emergency_halt in pre-commit hook."""
    print(
        """===== AM PIXEL COMMIT CHECK =====
1. Below 85/85 automated = REBUILD (not patch) [Constitution Rule 4]
2. Architecture = autoregressive palette-index tokens ONLY [Constitution Rule 2]
3. Every training sprite needs a PROVENANCE MANIFEST entry [Constitution Rule 5]
4. Speed is THIRD priority — never compromise accuracy [Constitution Rule 8]
5. DNA lock is IRREVERSIBLE — did you call compliance.dna_lock_gate()?
6. Transformative branch: use transformative_provenance_gate() and corpus_transformative/ [CHANGE-T04]
================================="""
    )


def run_pre_commit_hook() -> None:
    """Entry point for git pre-commit hook."""
    check_emergency_halt()
    print_pre_commit_banner()


if __name__ == "__main__":
    run_pre_commit_hook()
