"""Actual SQLite/crash/concurrency profile checks, without guest acceptance claims."""
import copy
import json
import multiprocessing
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime' / 'broker'))
from profiles import ProfileError, ProfileStore


def interrupted_apply(path, schema, files, ready):
    store = ProfileStore(Path(path), 'toddy-default', schema)
    revision, bundle, _ = store.validate(files)
    with store._transaction() as db:
        db.execute('INSERT INTO profile_revisions VALUES(?,?,?,?)', (revision, bundle, len(bundle.encode()), 2000))
        db.execute('UPDATE profile_current SET revision=? WHERE id=1', (revision,))
        ready.set()
        # Die with uncommitted revision and pointer; parent must recover old bytes.
        os._exit(19)


class ProfileStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'profile'
        self.schema = json.loads((ROOT / 'config/phase2/profile.schema.json').read_text())
        self.config = json.loads((ROOT / 'config/phase2/profile/config.json').read_text())
        self.files = {'config.json': json.dumps(self.config).encode(), 'SOUL.md': b'Be concise.'}
        self.store = ProfileStore(self.path, 'toddy-default', self.schema)
        self.first = self.store.apply(self.files, expected_revision=None)

    def tearDown(self):
        self.temp.cleanup()

    def changed(self, name='Second'):
        files = dict(self.files)
        config = copy.deepcopy(self.config)
        config['display_name'] = name
        files['config.json'] = json.dumps(config).encode()
        return files

    def test_atomic_revision_cas_restore_and_task_pinning(self):
        self.assertEqual(self.store.pin_task('task1', expected_revision=self.first), self.first)
        second = self.store.apply(self.changed(), expected_revision=self.first)
        self.assertNotEqual(second, self.first)
        revision, old = self.store.task_snapshot('task1')
        self.assertEqual(revision, self.first)
        self.assertEqual(old, self.files)
        # Repeat accepted task binding after the active profile changed.
        self.assertEqual(self.store.pin_task('task1', expected_revision=self.first), self.first)
        with self.assertRaisesRegex(ProfileError, 'task_profile_identity_conflict'):
            self.store.pin_task('task1', expected_revision=second)
        with self.assertRaisesRegex(ProfileError, 'stale_profile_revision'):
            self.store.pin_task('task2', expected_revision=self.first)
        with self.assertRaisesRegex(ProfileError, 'stale_profile_revision'):
            self.store.apply(self.changed('stale edit'), expected_revision=self.first)
        self.assertEqual(self.store.restore(self.first, expected_revision=second), self.first)
        self.assertEqual(self.store.snapshot(), self.files)
        reopened = ProfileStore(self.path, 'toddy-default', self.schema)
        self.assertEqual(reopened.task_snapshot('task1'), (self.first, self.files))
        with self.assertRaisesRegex(ProfileError, 'profile_store_identity_conflict'):
            ProfileStore(self.path, 'different-profile', self.schema)

    def test_invalid_edits_preserve_current_and_snapshot(self):
        candidates = []
        for mutate in (
            lambda c: c.update(schema_version=2),
            lambda c: c.update(root_grant=True),
            lambda c: c['budgets'].update(max_retries=3),
            lambda c: c['budgets'].update(max_retries=True),
            lambda c: c['provider'].update(allow_remote_fallback=True),
            lambda c: c['provider'].update(connection_ref='secret'),
            lambda c: c['tools'].update(enabled=['unavailable']),
            lambda c: c['extensions'].update(enabled=['unknown-code']),
            lambda c: c['automation'].update(workflow_ids=['do-root-things']),
            lambda c: c.update(profile_id='different-profile'),
        ):
            config = copy.deepcopy(self.config)
            mutate(config)
            candidates.append({'config.json': json.dumps(config).encode()})
        candidates += [
            {'config.json': b'{"schema_version":1,"schema_version":1}'},
            {'config.json': b'{"value":NaN}'},
            {'config.json': b'\xff'},
            dict(self.files, **{'../../outside': b'payload'}),
            dict(self.files, **{'skills/run/SKILL.md': b'unsupported import'}),
            dict(self.files, **{'SOUL.md': b'x' * 32769}),
        ]
        for files in candidates:
            with self.subTest(candidate=list(files)):
                with self.assertRaises(ProfileError):
                    self.store.apply(files, expected_revision=self.first)
                self.assertEqual(self.store.current(), self.first)
                self.assertEqual(self.store.snapshot(), self.files)

    def test_provider_configuration_requires_installed_adapter_and_opaque_ref(self):
        config = copy.deepcopy(self.config)
        config['provider'] = {'mode': 'local', 'adapter_id': 'local', 'model_id': 'fixture',
                              'connection_ref': 'local-owner-1', 'allow_remote_fallback': False}
        files = {'config.json': json.dumps(config).encode()}
        with self.assertRaisesRegex(ProfileError, 'unavailable_adapter'):
            self.store.validate(files)
        store = ProfileStore(self.path, 'toddy-default', self.schema,
                             capabilities={'adapters': {'local'}, 'tools': {'system-info'},
                                           'skills': {'explain-system'}})
        store.validate(files)
        config['provider']['connection_ref'] = 'https://user:token@example.invalid'
        with self.assertRaisesRegex(ProfileError, 'invalid_connection_reference'):
            store.validate({'config.json': json.dumps(config).encode()})
        config['provider']['connection_ref'] = 'local-owner-1'
        config['budgets']['remote_spending_enabled'] = True
        with self.assertRaises(ProfileError):
            store.validate({'config.json': json.dumps(config).encode()})

    def test_real_process_loss_before_commit_preserves_active_profile(self):
        ready = multiprocessing.Event()
        child = multiprocessing.Process(target=interrupted_apply,
            args=(str(self.path), self.schema, self.changed(), ready))
        child.start()
        child.join(5)
        if child.is_alive():
            child.terminate()
            child.join(5)
            self.fail('interrupted apply did not stop within bound')
        self.assertEqual(child.exitcode, 19)
        self.assertTrue(ready.is_set())
        reopened = ProfileStore(self.path, 'toddy-default', self.schema)
        self.assertEqual(reopened.current(), self.first)
        self.assertEqual(reopened.snapshot(), self.files)
        with reopened._db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM profile_revisions').fetchone()[0], 1)
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

    def test_two_concurrent_edits_exactly_one_wins(self):
        barrier = threading.Barrier(2)
        results = []
        def writer(name):
            store = ProfileStore(self.path, 'toddy-default', self.schema)
            barrier.wait(timeout=5)
            try:
                results.append(store.apply(self.changed(name), expected_revision=self.first))
            except ProfileError as error:
                results.append(str(error))
        threads = [threading.Thread(target=writer, args=(name,)) for name in ('left', 'right')]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(5)
            self.assertFalse(thread.is_alive())
        self.assertEqual(results.count('stale_profile_revision'), 1)
        self.assertIn(self.store.current(), results)

    def test_corrupt_snapshot_explicit_safe_recovery_no_activation_or_replay(self):
        self.store.pin_task('old-task', expected_revision=self.first)
        second = self.store.apply(self.changed(), expected_revision=self.first)
        with self.store._transaction() as db:
            db.execute('UPDATE profile_revisions SET bundle=? WHERE revision=?', ('{"config.json":"broken"}', second))
        with self.assertRaisesRegex(ProfileError, 'profile_revision_corrupt'):
            self.store.snapshot()
        recovery = self.store.recovery_snapshot()
        self.assertEqual(recovery['source_revision'], self.first)
        self.assertTrue(recovery['recovery_required'])
        config = json.loads(recovery['files']['config.json'])
        self.assertEqual(config['provider']['mode'], 'deferred')
        self.assertIsNone(config['provider']['connection_ref'])
        self.assertFalse(config['automation']['enabled'])
        for group in ('tools', 'skills', 'extensions'):
            self.assertEqual(config[group]['enabled'], [])
        self.assertEqual(self.store.current(), second)  # Explicit owner review still needed.
        self.assertEqual(self.store.task_snapshot('old-task'), (self.first, self.files))

    def test_full_revision_store_refuses_without_deleting_pinned_or_active_bytes(self):
        self.store.pin_task('task1', expected_revision=self.first)
        small = ProfileStore(self.path, 'toddy-default', self.schema, revision_limit=2)
        second = small.apply(self.changed(), expected_revision=self.first)
        with self.assertRaisesRegex(ProfileError, 'profile_revision_storage_full'):
            small.apply(self.changed('third'), expected_revision=second)
        self.assertEqual(small.current(), second)
        self.assertEqual(small.task_snapshot('task1'), (self.first, self.files))
        self.assertEqual(small.restore(self.first, expected_revision=second), self.first)
        # Byte limit includes JSON escaping, not only unescaped document length.
        small = ProfileStore(self.path, 'toddy-default', self.schema, byte_limit=65536)
        escaped = self.changed('escaped'); escaped['SOUL.md'] = b'\0' * 32768
        with self.assertRaisesRegex(ProfileError, 'profile_revision_storage_full'):
            small.apply(escaped, expected_revision=self.first)
        self.assertEqual(small.current(), self.first)

    def test_noncanonical_paths_permissions_symlink_and_hardlink_refused(self):
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.path / 'state.sqlite').stat().st_mode & 0o777, 0o600)
        self.path.chmod(0o755)
        with self.assertRaisesRegex(ProfileError, 'unsafe_profile_store'):
            ProfileStore(self.path, 'toddy-default', self.schema)
        self.path.chmod(0o700)
        alias = self.path.parent / 'alias'
        alias.symlink_to(self.path, target_is_directory=True)
        with self.assertRaisesRegex(ProfileError, 'unsafe_profile_store'):
            ProfileStore(alias, 'toddy-default', self.schema)
        other = self.path.parent / 'linked'; other.mkdir(mode=0o700)
        os.link(self.path / 'state.sqlite', other / 'state.sqlite')
        with self.assertRaisesRegex(ProfileError, 'unsafe_profile_database'):
            ProfileStore(other, 'toddy-default', self.schema)

    def test_future_schema_rules_fail_closed(self):
        schema = copy.deepcopy(self.schema)
        schema['allOf'].append({'if': {'unevaluatedProperties': False}, 'then': {}})
        store = ProfileStore(self.path, 'toddy-default', schema)
        with self.assertRaisesRegex(ProfileError, 'unsupported_profile_schema'):
            store.validate(self.files)


if __name__ == '__main__':
    unittest.main(verbosity=2)
