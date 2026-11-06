"""Protect evidence and dependency gates from accidental false completion."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("project", ROOT / "scripts/project.py")
project = importlib.util.module_from_spec(spec)
spec.loader.exec_module(project)


class ProgressGates(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "status.json").read_text())
        # Tests use an unstarted fixture even as the real project progresses.
        for row in self.data["milestones"]:
            row["status"], row["evidence"] = "not_started", []
        self.data["gates"] = {"G1": "pending", "G2": "pending"}

    def test_unstarted_baseline_has_zero_os_progress(self):
        project.validate(self.data)
        self.assertEqual(project.percentages(self.data), {"foundation": 0, "agentic": 0})

    def test_cannot_complete_without_evidence(self):
        self.data["milestones"][0]["status"] = "completed"
        with self.assertRaisesRegex(ValueError, "no evidence"):
            project.validate(self.data)

    def test_cannot_start_before_prerequisites(self):
        self.data["milestones"][1]["status"] = "in_progress"
        with self.assertRaisesRegex(ValueError, "Unfinished prerequisites"):
            project.validate(self.data)

    def test_cycle_rejected(self):
        self.data["milestones"][0]["depends_on"] = ["H02"]
        with self.assertRaisesRegex(ValueError, "cycle"):
            project.validate(self.data)

    def test_wrong_weights_rejected(self):
        self.data["milestones"][0]["weight"] += 1
        with self.assertRaisesRegex(ValueError, "total 100"):
            project.validate(self.data)

    def test_evidence_cannot_escape_repository(self):
        self.data["milestones"][0]["evidence"] = ["../not-project-evidence.md"]
        with self.assertRaisesRegex(ValueError, "out-of-repository"):
            project.validate(self.data)

    def test_gate_cannot_claim_pass_without_completion(self):
        self.data["gates"]["G1"] = "passed"
        with self.assertRaisesRegex(ValueError, "Inconsistent gate"):
            project.validate(self.data)


if __name__ == "__main__":
    unittest.main()
