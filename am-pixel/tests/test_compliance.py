"""Tests for tools/compliance.py and training gates (CHANGE-028)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class EmergencyHaltTests(unittest.TestCase):
    def test_check_emergency_halt_exits_when_file_exists(self) -> None:
        from tools import compliance

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "EMERGENCY_HALT").write_text("test halt", encoding="utf-8")
            with patch.object(compliance, "REPO_ROOT", root):
                with self.assertRaises(SystemExit) as ctx:
                    compliance.check_emergency_halt()
                self.assertEqual(ctx.exception.code, 2)

    def test_check_emergency_halt_passes_when_missing(self) -> None:
        from tools import compliance

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(compliance, "REPO_ROOT", Path(tmp)):
                compliance.check_emergency_halt()


class DnaLockGateTests(unittest.TestCase):
    def test_literal_confirmation(self) -> None:
        from tools import compliance

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(compliance, "REPO_ROOT", Path(tmp)):
                self.assertTrue(
                    compliance.dna_lock_gate("sam_vendor", "CONFIRM LOCK sam_vendor"),
                )
                self.assertFalse(
                    compliance.dna_lock_gate("sam_vendor", "confirm lock sam_vendor"),
                )


class TrainingRunGateTests(unittest.TestCase):
    def test_fails_without_manifest_entries(self) -> None:
        from tools import compliance

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            am = root / "am-pixel"
            (am / "model" / "architecture").mkdir(parents=True)
            (am / "logs").mkdir(parents=True)
            (am / "data").mkdir(parents=True)
            (am / "model" / "architecture" / "IMPLEMENTATION_NOTES.md").write_text("ok", encoding="utf-8")
            (am / "logs" / "phase_gates.md").write_text(
                "PHASE4_ARCHITECTURE_REVIEW: APPROVED\n",
                encoding="utf-8",
            )
            (am / "data" / "TRAINING_PROVENANCE_MANIFEST.json").write_text("[]", encoding="utf-8")
            with patch.object(compliance, "REPO_ROOT", root):
                self.assertFalse(
                    compliance.training_run_gate(
                        repo_root=root,
                        manifest_path=am / "data" / "TRAINING_PROVENANCE_MANIFEST.json",
                        phase_gates_path=am / "logs" / "phase_gates.md",
                        implementation_notes_path=am / "model" / "architecture" / "IMPLEMENTATION_NOTES.md",
                    ),
                )

    def test_passes_with_manifest_and_approval(self) -> None:
        from tools import compliance

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            am = root / "am-pixel"
            (am / "model" / "architecture").mkdir(parents=True)
            (am / "logs").mkdir(parents=True)
            (am / "data").mkdir(parents=True)
            (am / "model" / "architecture" / "IMPLEMENTATION_NOTES.md").write_text("ok", encoding="utf-8")
            (am / "logs" / "phase_gates.md").write_text(
                "PHASE4_ARCHITECTURE_REVIEW: APPROVED\n",
                encoding="utf-8",
            )
            manifest = [{"sprite_id": "t1", "source_url": "x", "license": "CC0"}]
            (am / "data" / "TRAINING_PROVENANCE_MANIFEST.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )
            with patch.object(compliance, "REPO_ROOT", root):
                self.assertTrue(
                    compliance.training_run_gate(
                        repo_root=root,
                        manifest_path=am / "data" / "TRAINING_PROVENANCE_MANIFEST.json",
                        phase_gates_path=am / "logs" / "phase_gates.md",
                        implementation_notes_path=am / "model" / "architecture" / "IMPLEMENTATION_NOTES.md",
                    ),
                )


class ProvenanceGateTests(unittest.TestCase):
    def test_requires_sprite_id_in_manifest(self) -> None:
        from tools import compliance

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            am = root / "am-pixel"
            am.mkdir(parents=True)
            mpath = am / "TRAINING_PROVENANCE_MANIFEST.json"
            mpath.write_text(json.dumps([{"sprite_id": "a"}]), encoding="utf-8")
            with patch.object(compliance, "REPO_ROOT", root):
                self.assertTrue(compliance.provenance_gate("a", manifest_path=mpath))
                self.assertFalse(compliance.provenance_gate("missing", manifest_path=mpath))


if __name__ == "__main__":
    unittest.main()
