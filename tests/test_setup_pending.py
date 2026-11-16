"""Host checks for private intent custody; no package/guest/UI acceptance."""
import copy
import importlib.util
import fcntl
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('setup_pending', ROOT / 'runtime/setup/pending.py')
pending = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pending)


class PendingChoices(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'setup'
        self.catalog = pending.Catalog((ROOT / 'config/phase2/software-catalog.json').read_bytes())
        self.store = pending.PendingStore(self.path, self.catalog)
        self.addCleanup(self.store.close)
        self.revision = self.store.create('test-installation')

    def test_empty_later_is_private_and_survives_reopen_without_agent(self):
        value, revision = self.store.load()
        self.assertEqual(revision, self.revision)
        self.assertEqual(value['ai_choice'], 'later')
        self.assertEqual(value['choices'], [])
        self.assertEqual(value['consent_receipts'], [])
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.path / 'pending.json').stat().st_mode), 0o600)
        changed = self.store.dismiss(expected_revision=revision)
        with pending.PendingStore(self.path, self.catalog) as reopened:
            result, actual = reopened.load()
        self.assertTrue(result['invitation_dismissed'])
        self.assertEqual(changed, actual)

    def test_deferred_handoff_is_intent_and_catalog_candidates_remain_unavailable(self):
        value, revision = self.store.load()
        value['ai_choice'] = 'local'
        value['choices'] = [{'id': 'docker', 'artifact_id': None,
                             'state': 'deferred', 'error_code': 'offline'}]
        self.store.save(value, expected_revision=revision)
        result, _ = self.store.load()
        review = self.catalog.review(result)
        self.assertEqual(review[0]['availability'], 'unavailable')
        self.assertEqual(review[0]['reason'], 'no_verified_release')
        self.assertFalse(review[0]['can_install'])
        value['catalog_revision'] = 'a' * 64
        self.assertTrue(self.catalog.review(value)[0]['catalog_changed'])

    def test_duplicate_create_and_stale_editor_cannot_overwrite_newer_intent(self):
        original, revision = self.store.load()
        with self.assertRaisesRegex(pending.SetupError, 'stale_revision'):
            self.store.create('test-installation')
        self.store.dismiss(expected_revision=revision)
        with self.assertRaisesRegex(pending.SetupError, 'stale_revision'):
            self.store.save(original, expected_revision=revision)
        self.assertTrue(self.store.load()[0]['invitation_dismissed'])

    def test_failed_atomic_replace_preserves_last_valid_manifest(self):
        original = (self.path / 'pending.json').read_bytes()
        value, revision = self.store.load()
        value['ai_choice'] = 'api'
        with mock.patch.object(pending.os, 'replace', side_effect=OSError('injected-before-commit')):
            with self.assertRaises(OSError):
                self.store.save(value, expected_revision=revision)
        self.assertEqual((self.path / 'pending.json').read_bytes(), original)
        self.assertFalse(list(self.path.glob('.pending-*')))
        self.assertEqual(self.store.load()[0]['ai_choice'], 'later')

    def test_secrets_grants_unknown_choices_base_and_fabricated_installed_rejected(self):
        original, revision = self.store.load()
        invalid = []
        for field, value in [('api_key', 'dummy'), ('grants', ['root']),
                             ('consent_receipts', [{'grant': 'root'}]),
                             ('schema_version', True), ('installation_id', 'changed')]:
            row = copy.deepcopy(original)
            row[field] = value
            invalid.append(row)
        for app, state, artifact, error in [('git', 'deferred', None, None),
                                           ('unknown', 'deferred', None, None),
                                           ('docker', 'installed', None, None),
                                           ('docker', 'installing', None, None),
                                           ('docker', 'selected', None, None),
                                           ('docker', 'deferred', 'guessed-artifact', None),
                                           ('docker', 'deferred', None, {'raw': 'secret'})]:
            row = copy.deepcopy(original)
            row['choices'] = [{'id': app, 'state': state, 'artifact_id': artifact, 'error_code': error}]
            invalid.append(row)
        for row in invalid:
            with self.subTest(row=row), self.assertRaises(pending.SetupError):
                self.store.save(row, expected_revision=revision)
        self.assertEqual(self.store.load()[0], original)

    def test_duplicate_json_oversize_and_nonfinite_fail_without_repairing_evidence(self):
        state = self.path / 'pending.json'
        for bad in [b'{"schema_version":1,"schema_version":1}', b'[' * 5000,
                    b'{"schema_version":NaN}', b'X' * (pending.MAX_BYTES + 1), b'\xff']:
            state.write_bytes(bad)
            with self.subTest(bad=bad[:50]), self.assertRaises(pending.SetupError):
                self.store.load()
            self.assertEqual(state.read_bytes(), bad)

    def test_symlink_and_shared_mode_and_hardlink_are_refused(self):
        state = self.path / 'pending.json'
        original = state.read_bytes()
        outside = Path(self.temp.name) / 'outside'
        outside.write_bytes(original)
        outside.chmod(0o600)
        state.unlink()
        state.symlink_to(outside)
        with self.assertRaises((OSError, pending.SetupError)):
            self.store.load()
        state.unlink()
        os.link(outside, state)
        with self.assertRaisesRegex(pending.SetupError, 'state_file'):
            self.store.load()
        state.unlink()
        state.write_bytes(original)
        state.chmod(0o644)
        with self.assertRaisesRegex(pending.SetupError, 'state_file'):
            self.store.load()
        self.assertEqual(outside.read_bytes(), original)

    def test_directory_symlink_or_insecure_permissions_are_refused(self):
        link = Path(self.temp.name) / 'link'
        link.symlink_to(self.path, target_is_directory=True)
        with self.assertRaisesRegex(pending.SetupError, 'state_directory'):
            pending.PendingStore(link, self.catalog)
        self.path.chmod(0o755)
        with self.assertRaisesRegex(pending.SetupError, 'state_directory'):
            pending.PendingStore(self.path, self.catalog)

    def test_other_controller_lock_returns_busy_instead_of_blocking_ui(self):
        with (self.path / '.pending.lock').open('r+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(pending.SetupError, 'setup_busy'):
                self.store.load()
        self.assertEqual(self.store.load()[1], self.revision)

    def test_unverified_qualified_release_metadata_cannot_enable_install(self):
        source = json.loads((ROOT / 'config/phase2/software-catalog.json').read_bytes())
        source['qualified_releases'] = [{'id': 'docker', 'trusted': True}]
        with self.assertRaisesRegex(pending.SetupError, 'release_verification_required'):
            pending.Catalog(json.dumps(source).encode())


if __name__ == '__main__':
    unittest.main()
