"""Atomic canonical memory/profile integration, no native/IPC acceptance claim."""
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime/broker'))
from memory_api import (MemoryAPI, MemoryAPIError, MemoryEngine, EMPTY_USER_DOCUMENT,
                       LEGACY_EMPTY_USER_DOCUMENT, parse_projection, render_projection)
from profiles import ProfileStore, ProfileError


class MemoryAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.schema = json.loads((ROOT / 'config/phase2/profile.schema.json').read_text())
        self.config = json.loads((ROOT / 'config/phase2/profile/config.json').read_text())
        self.files = {'config.json': json.dumps(self.config).encode(), 'SOUL.md': b'Keep it concise.',
                      'USER.md': EMPTY_USER_DOCUMENT}
        self.now = 1000.
        self.allowed = True
        self.store = ProfileStore(self.directory / 'default', 'toddy-default', self.schema, revision_limit=64,
            clock=lambda: self.now)
        self.initial = self.store.apply(self.files, expected_revision=None)
        self.api = MemoryAPI(self.store, owner_allowed=lambda: self.allowed, clock=lambda: self.now)

    def tearDown(self):
        self.temp.cleanup()

    def put(self, key='language', text='Portuguese', **kwargs):
        return self.api.put(key, text, expected_revision=self.store.current(), **kwargs)

    def test_crud_projection_cas_and_immutable_pins_use_one_database(self):
        first = self.put()
        self.assertEqual(parse_projection(self.store.snapshot()['USER.md']), {'language': 'Portuguese'})
        self.store.pin_task('task-original', expected_revision=first['profile_revision'])
        second = self.put(text='English')
        self.assertEqual(self.api.inspect()['records'][0]['text'], 'English')
        with self.assertRaisesRegex(ProfileError, 'stale_profile'):
            self.api.delete('language', expected_revision=first['profile_revision'])
        self.api.delete('language', expected_revision=second['profile_revision'])
        self.assertEqual(parse_projection(self.store.snapshot()['USER.md']), {})
        self.assertIn(b'Portuguese', self.store.task_snapshot('task-original')[1]['USER.md'])
        self.assertEqual(list((self.directory / 'default').glob('*.sqlite')), [self.store.path])

    def test_current_canonical_context_replaces_old_pinned_or_raw_user_text(self):
        self.put()
        revision = self.store.current()
        self.store.pin_task('task-original', expected_revision=revision)
        old_files = self.store.task_snapshot('task-original')[1]
        self.api.delete('language', expected_revision=revision)
        captured = []
        class Engine:
            def available(self, profile):
                return True
            def __call__(self, files, revision, task, text, consent, tool, output, canceled):
                captured.append(files['USER.md'])
                self.revision = revision
                return {'state': 'completed'}
        engine = Engine()
        wrapped = MemoryEngine(engine, self.api)
        self.assertTrue(wrapped.available(self.config))
        result = wrapped(old_files, revision, 'task-original', 'Hello', False, lambda *_: self.fail(), lambda _: None, lambda: False)
        self.assertEqual(result['state'], 'completed')
        self.assertNotIn(b'Portuguese', captured[0])
        self.assertEqual(engine.revision, revision)  # other pinned configuration is preserved
        self.assertIn(b'Portuguese', old_files['USER.md'])  # immutable historical source remains unchanged

    def test_generation_change_stops_output_and_independently_denies_next_effect(self):
        self.put()
        api, store = self.api, self.store
        effects, output = [], []
        class Engine:
            def __call__(self, files, revision, task, text, consent, tool, append, canceled):
                self.initial = files['USER.md']
                api.delete('language', expected_revision=store.current())
                self.assert_canceled = canceled()
                self.denied = tool('call-one', 'file-write', {'text': 'effect'})
                append('stale preference output')
                return {'state': 'completed'}  # an engine completion cannot override cancellation
        engine = Engine()
        result = MemoryEngine(engine, self.api)(self.store.snapshot(), self.store.current(), 'task', 'Hello', False,
            lambda *_: effects.append('effect'), output.append, lambda: False)
        self.assertIn(b'Portuguese', engine.initial)
        self.assertTrue(engine.assert_canceled)
        self.assertEqual(engine.denied['outcome'], 'rejected')
        self.assertEqual(result['state'], 'canceled')
        self.assertEqual(effects, [])
        self.assertEqual(output, [])

    def test_manual_user_notes_are_preserved_until_review_and_never_auto_hydrated(self):
        manual = b'Owner manual notes: keep the project on the blue drive.\n'
        files = dict(self.store.snapshot(), **{'USER.md': manual})
        revision = self.store.apply(files, expected_revision=self.store.current())
        self.assertTrue(self.api.inspect()['user_document_review_required'])
        with self.assertRaisesRegex(MemoryAPIError, 'review_required'):
            self.put()
        self.assertEqual(self.store.snapshot()['USER.md'], manual)
        self.assertNotIn(b'blue drive', self.api.context_snapshot()['user_document'])
        with self.assertRaisesRegex(MemoryAPIError, 'document_changed'):
            self.api.review_user_document({'drive': 'Use the blue drive'}, expected_revision=revision, reviewed_user_sha256='a' * 64)
        result = self.api.review_user_document({'drive': 'Use the blue drive'}, expected_revision=revision,
            reviewed_user_sha256=hashlib.sha256(manual).hexdigest())
        self.assertTrue(result['previous_user_document_preserved'])
        self.assertEqual(self.store.snapshot(revision)['USER.md'], manual)
        self.assertEqual(parse_projection(self.store.snapshot()['USER.md']), {'drive': 'Use the blue drive'})

    def test_stale_reviewed_projection_and_old_backup_cannot_revive_deleted_preference(self):
        self.put()
        old_document = self.store.snapshot()['USER.md']
        old_export = self.api.export()
        self.api.delete('language', expected_revision=self.store.current())
        candidate = dict(self.store.snapshot(), **{'USER.md': old_document})
        result = self.api.apply_profile(candidate, expected_revision=self.store.current(),
            reviewed_user_sha256=hashlib.sha256(old_document).hexdigest())
        self.assertEqual(result['records'], [])
        self.assertEqual(parse_projection(self.store.snapshot()['USER.md']), {})
        self.api.restore(old_export, expected_revision=self.store.current())
        self.assertEqual(self.api.inspect()['records'], [])
        self.put(text='Portuguese again')  # deliberate explicit owner put can revive
        self.assertEqual(self.api.inspect()['records'][0]['text'], 'Portuguese again')

    def test_profile_storage_failure_rolls_back_canonical_delete_and_generation(self):
        self.store.revision_limit = 3
        self.put()
        self.put('editor', 'Vim')
        before = self.api.inspect()
        raw = self.store.snapshot()['USER.md']
        with self.assertRaisesRegex(ProfileError, 'storage_full'):
            self.api.delete('language', expected_revision=self.store.current())
        self.assertEqual(self.api.inspect(), before)
        self.assertEqual(self.store.snapshot()['USER.md'], raw)
        with self.store._db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM memory_deleted').fetchone()[0], 0)

    def test_user_projection_capacity_failure_rolls_back_new_record_and_profile(self):
        preferences = {'pref-' + str(index): 'x' * 4096 for index in range(7)}
        self.api.review_user_document(preferences, expected_revision=self.store.current(),
            reviewed_user_sha256=hashlib.sha256(EMPTY_USER_DOCUMENT).hexdigest())
        before = self.api.inspect()
        with self.assertRaisesRegex(MemoryAPIError, 'projection_capacity'):
            self.put('pref-eight', 'x' * 4096)
        self.assertEqual(self.api.inspect(), before)

    def test_existing_semantic_validation_and_outer_transaction_rollback_are_preserved(self):
        self.put()
        before = self.api.inspect()
        candidate = self.store.snapshot()
        config = json.loads(candidate['config.json'])
        config['budgets']['max_retries'] = 3
        candidate['config.json'] = json.dumps(config).encode()
        with self.assertRaises(ProfileError):
            self.api.apply_profile(candidate, expected_revision=self.store.current())
        self.assertEqual(self.api.inspect(), before)
        config = json.loads(self.store.snapshot()['config.json'])
        config['display_name'] = 'New persona name for future tasks'
        valid = dict(self.store.snapshot(), **{'config.json': json.dumps(config).encode()})
        result = self.api.apply_profile(valid, expected_revision=self.store.current())
        self.assertEqual(result['memory_generation'], before['memory_generation'])
        with self.store._db() as db:
            with self.assertRaisesRegex(ProfileError, 'transaction_required'):
                self.store.apply_in_transaction(db, self.store.snapshot(), expected_revision=self.store.current())
        other = sqlite3.connect(':memory:')
        try:
            other.execute('BEGIN')
            with self.assertRaisesRegex(ProfileError, 'database_mismatch'):
                self.store.apply_in_transaction(other, self.store.snapshot(), expected_revision=self.store.current())
        finally:
            other.close()

    def test_two_profiles_keep_memory_context_and_revisions_independent(self):
        self.put()
        config = copy.deepcopy(self.config)
        config['profile_id'] = 'other-profile'
        store = ProfileStore(self.directory / 'other', 'other-profile', self.schema)
        store.apply(dict(self.files, **{'config.json': json.dumps(config).encode()}), expected_revision=None)
        other = MemoryAPI(store, owner_allowed=lambda: True, clock=lambda: self.now)
        other.put('language', 'Japanese', expected_revision=store.current())
        self.assertNotIn(b'Japanese', self.api.context_snapshot()['user_document'])
        self.assertNotIn(b'Portuguese', other.context_snapshot()['user_document'])
        self.assertNotEqual(self.store.current(), store.current())

    def test_expiry_export_is_read_only_and_old_backup_does_not_remove_retention(self):
        self.put(expires=1001)
        old = self.api.export()
        generation, revision = self.api.generation(), self.store.current()
        self.now = 1001
        exported = json.loads(self.api.export())
        self.assertEqual(exported['records'], [])
        self.assertEqual(exported['deleted'][0]['id'], 'language')
        self.assertEqual(self.api.generation(), generation)
        self.assertEqual(self.store.current(), revision)
        self.assertNotIn(b'Portuguese', self.api.context_snapshot()['user_document'])
        self.api.restore(old, expected_revision=revision)
        self.assertEqual(self.api.inspect()['records'], [])
        self.assertEqual(parse_projection(self.store.snapshot()['USER.md']), {})

    def test_current_owner_required_and_known_empty_template_is_not_lost_manual_data(self):
        self.allowed = False
        for operation in (self.api.inspect, self.api.export, self.api.context_snapshot, self.put):
            with self.assertRaisesRegex(MemoryAPIError, 'authenticated_owner'):
                operation()
        self.allowed = True
        files = dict(self.files, **{'USER.md': LEGACY_EMPTY_USER_DOCUMENT})
        self.store.apply(files, expected_revision=self.store.current())
        self.put()
        self.assertFalse(self.api.inspect()['user_document_review_required'])

    def test_manual_projection_conflict_blocks_stale_preference_egress_until_review(self):
        self.put()
        manually_changed = dict(self.store.snapshot(), **{'USER.md': EMPTY_USER_DOCUMENT})
        self.store.apply(manually_changed, expected_revision=self.store.current())
        with self.assertRaisesRegex(MemoryAPIError, 'review_required'):
            self.api.context_snapshot()
        self.assertEqual(self.api.inspect()['records'][0]['text'], 'Portuguese')  # preserved, not silently lost
        self.api.review_user_document({}, expected_revision=self.store.current(),
            reviewed_user_sha256=hashlib.sha256(EMPTY_USER_DOCUMENT).hexdigest())
        self.assertNotIn(b'Portuguese', self.api.context_snapshot()['user_document'])

    def test_engine_binding_cannot_mix_another_profile_memory(self):
        config = copy.deepcopy(self.config)
        config['profile_id'] = 'different-profile'
        class Engine:
            def available(self, profile):
                return True
            def __call__(self, *args):
                raise AssertionError('cross-profile engine invoked')
        wrapped = MemoryEngine(Engine(), self.api)
        self.assertFalse(wrapped.available(config))
        with self.assertRaisesRegex(MemoryAPIError, 'profile_context_mismatch'):
            wrapped(dict(self.files, **{'config.json': json.dumps(config).encode()}), self.initial, 'task', 'Hello', False,
                lambda *_: self.fail(), lambda _: self.fail(), lambda: False)

    def test_two_api_objects_serialize_delete_with_already_admitted_write(self):
        self.put()
        second = MemoryAPI(self.store, owner_allowed=lambda: True, clock=lambda: self.now)
        self.assertIs(self.api._admission, second._admission)
        entered, release = threading.Event(), threading.Event()
        results, errors, effects = [], [], []
        class Engine:
            def __call__(self, files, revision, task, text, consent, tool, append, canceled):
                tool('call', 'file-write', {})
                return {'state': 'completed'}
        def effect(*_):
            entered.set()
            if not release.wait(3):
                raise AssertionError('test did not release admitted write')
            effects.append('committed fixture effect')
            return {'outcome': 'verified'}
        def run():
            try:
                results.append(MemoryEngine(Engine(), self.api)(self.store.snapshot(), self.store.current(),
                    'task', 'Hello', False, effect, lambda _: None, lambda: False))
            except BaseException as exc:
                errors.append(exc)
        worker = threading.Thread(target=run)
        worker.start()
        try:
            self.assertTrue(entered.wait(3))
            with self.assertRaisesRegex(MemoryAPIError, 'safe_boundary_required'):
                second.delete('language', expected_revision=self.store.current())
            self.assertEqual(self.api.inspect()['records'][0]['text'], 'Portuguese')
        finally:
            release.set()
            worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(effects, ['committed fixture effect'])
        self.assertEqual(results[0]['state'], 'completed')
        second.delete('language', expected_revision=self.store.current())
        self.assertNotIn(b'Portuguese', self.api.context_snapshot()['user_document'])


if __name__ == '__main__':
    unittest.main()
