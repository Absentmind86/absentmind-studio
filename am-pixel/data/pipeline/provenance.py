"""
Provenance manifest write-safety (CHANGE-034).

Canonical committed format stays the human-reviewable JSON array at
data/TRAINING_PROVENANCE_MANIFEST.json. Every write FIRST appends to the
append-only JSONL journal (crash-safe), THEN atomically rewrites the array
(temp file + os.replace). On divergence the journal is authoritative.

The manifest is a legal ledger (SPEC §15 / Constitution Rule 5):
- entries are never deleted or mutated — corrections are new entries with
  "supersedes": <sprite_id>;
- this module refuses to shrink the manifest.

Tier semantics: 1 = Golden Dataset, 2 = broad corpus,
0 = synthetic validation corpus (CHANGE-037; never production training data).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

_AM_PIXEL = Path(__file__).resolve().parent.parent.parent
DEFAULT_MANIFEST = _AM_PIXEL / "data" / "TRAINING_PROVENANCE_MANIFEST.json"

REQUIRED_FIELDS = ("sprite_id", "source_url", "creator", "license", "date_added", "tier")
ACCEPTABLE_LICENSES = {
    "CC0",
    "CC-BY",
    "commissioned-work-for-hire",
    # CHANGE-037 — tier 0 only, never production training data:
    "synthetic-validation",
}
# CHANGE-038: CC-BY-SA is on hold pending legal review — deliberately absent.


def _journal_path(manifest_path: Path) -> Path:
    return manifest_path.with_suffix(".jsonl")


def load(manifest_path: Path | None = None) -> list[dict]:
    path = manifest_path or DEFAULT_MANIFEST
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def load_journal(manifest_path: Path | None = None) -> list[dict]:
    path = _journal_path(manifest_path or DEFAULT_MANIFEST)
    if not path.is_file():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def has(sprite_id: str, manifest_path: Path | None = None) -> bool:
    return any(e.get("sprite_id") == sprite_id for e in load(manifest_path))


def validate_entry(entry: dict) -> list[str]:
    """Return a list of problems; empty list = valid."""
    problems = [f"missing required field: {f}" for f in REQUIRED_FIELDS if not entry.get(f) and entry.get(f) != 0]
    lic = entry.get("license")
    tier = entry.get("tier")
    if lic and lic not in ACCEPTABLE_LICENSES:
        problems.append(
            f"license {lic!r} not acceptable (SPEC §15; CC-BY-SA is on legal hold per CHANGE-038)"
        )
    if lic == "synthetic-validation" and tier != 0:
        problems.append("synthetic-validation license requires tier 0 (CHANGE-037)")
    if tier == 0 and lic != "synthetic-validation":
        problems.append("tier 0 entries must use license 'synthetic-validation' (CHANGE-037)")
    if tier not in (0, 1, 2):
        problems.append(f"tier must be 0, 1, or 2 — got {tier!r}")
    return problems


def append(entry: dict, manifest_path: Path | None = None) -> None:
    """
    Journal-first, then atomic array rewrite. Raises ValueError on invalid
    entries or duplicate sprite_id. Never shrinks the manifest.
    """
    path = manifest_path or DEFAULT_MANIFEST
    problems = validate_entry(entry)
    if problems:
        raise ValueError(f"invalid provenance entry: {problems}")
    current = load(path)
    if any(e.get("sprite_id") == entry["sprite_id"] for e in current):
        raise ValueError(f"duplicate sprite_id: {entry['sprite_id']}")

    journal = _journal_path(path)
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())

    _atomic_write_array(path, current + [entry])


def _atomic_write_array(path: Path, entries: list[dict]) -> None:
    existing = load(path) if path.is_file() else []
    if len(entries) < len(existing):
        raise ValueError(
            "refusing to shrink the provenance manifest "
            f"({len(existing)} -> {len(entries)} entries) — Constitution Rule 5"
        )
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def rebuild_from_journal(manifest_path: Path | None = None) -> int:
    """Rebuild the canonical array from the journal (journal is authoritative).
    Returns the number of entries. Used after a detected divergence/corruption."""
    path = manifest_path or DEFAULT_MANIFEST
    entries: dict[str, dict] = {}
    for e in load_journal(path):
        entries[e["sprite_id"]] = e
    merged = list(entries.values())
    # never lose array-only entries (e.g. journal introduced after array existed)
    try:
        for e in load(path):
            entries.setdefault(e["sprite_id"], e)
        merged = list(entries.values())
    except (ValueError, json.JSONDecodeError):
        pass  # corrupted array is exactly the case the journal exists for
    _atomic_write_array_force(path, merged)
    return len(merged)


def _atomic_write_array_force(path: Path, entries: list[dict]) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def production_entries(manifest_path: Path | None = None) -> list[dict]:
    """Entries eligible for production training (tier 1 and 2 only — CHANGE-037)."""
    return [e for e in load(manifest_path) if e.get("tier") in (1, 2)]
