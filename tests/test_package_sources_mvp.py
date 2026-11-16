import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/build/phase2'))
import package_sources_mvp as mvp


class MVPSourceReviewTests(unittest.TestCase):
    def project(self, directory, required=()):
        root = Path(directory)
        subprocess.run(['git', 'init', '-q', str(root)], check=True)
        def git(*args):
            return subprocess.check_output(['git', *args], cwd=root).decode().strip()
        git('config', 'user.name', 'Unqualified fixture')
        git('config', 'user.email', 'fixture@example.invalid')
        path = root / 'scripts/build/example.py'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'current fixture build script\n')
        git('add', '.')
        git('commit', '-qm', 'Unqualified current source fixture')
        return mvp.ReviewProject(root, git('rev-parse', 'HEAD'), set(required), {}, set())

    def test_current_script_and_missing_broad_snapshot_are_explicit_not_source_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            item = project.source('scripts/build/example.py', 'a' * 64)
            self.assertEqual(item.origin['kind'], 'current-functional-script-review-required')
            another = project.source('scripts/build/example.py', 'd' * 64)
            self.assertEqual(item.description(), another.description())
            self.assertEqual(project.ledger[('scripts/build/example.py', 'd' * 64)]['recorded_sha256'], 'd' * 64)
            self.assertEqual(project.ledger[('scripts/build/example.py', 'a' * 64)]['recorded_sha256'], 'a' * 64)
            missing = project.source('scripts/build/removed.py', 'b' * 64)
            self.assertEqual(missing.origin['kind'], 'unresolved-fingerprint-ledger-not-source')
            with self.assertRaises(ValueError):
                project.source('native-inputs/private-key', 'c' * 64)

    def test_original_preferred_input_never_uses_current_replacement_and_draft_cannot_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory, {('scripts/build/example.py', 'a' * 64)})
            with self.assertRaisesRegex(ValueError, 'Missing exact'):
                project.source('scripts/build/example.py', 'a' * 64)
            inventory = Path(directory) / 'review.json'
            inventory.write_text(json.dumps({'kind': mvp.KIND}))
            with self.assertRaisesRegex(ValueError, 'Actual selected corresponding-source inventory required'):
                mvp.strict.verify_assets(inventory, [], {}, project.commit)
