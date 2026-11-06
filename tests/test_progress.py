"""Protect evidence and dependency gates from accidental false completion."""
import copy
import importlib.util
import json
import unittest
import subprocess
import tempfile
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


class DocumentationLinks(unittest.TestCase):
    def test_ignored_sources_are_excluded_but_untracked_docs_are_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', directory], check=True)
            (root/'.gitignore').write_text('.local/\n')
            source=root/'.local/source';source.mkdir(parents=True)
            (source/'README.md').write_text('[upstream](missing.md)')
            (root/'README.md').write_text('[valid](.gitignore)')
            project.check_links(root)
            (root/'new.md').write_text('[broken](missing.md)')
            with self.assertRaisesRegex(ValueError, 'Broken local link in new.md'):
                project.check_links(root)

    def test_tracked_docs_remain_checked_even_if_later_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            subprocess.run(['git','init','-q',directory],check=True)
            (root/'tracked.md').write_text('[broken](missing.md)')
            subprocess.run(['git','add','tracked.md'],cwd=root,check=True)
            (root/'.gitignore').write_text('tracked.md\n')
            with self.assertRaisesRegex(ValueError,'Broken local link in tracked.md'):
                project.check_links(root)


if __name__ == "__main__":
    unittest.main()
