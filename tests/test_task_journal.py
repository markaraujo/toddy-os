"""Durable request/effect/Stop boundaries on actual private SQLite databases."""
import json
import multiprocessing
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime/broker'))
from profiles import ProfileStore
from tasks import TaskError, TaskJournal


def lost_after_effect(directory, schema, task_id, marker):
    profiles = ProfileStore(Path(directory), 'toddy-default', schema)
    journal = TaskJournal(profiles)
    def apply(*_):
        with open(marker, 'w') as output:
            output.write('effect-once')
            output.flush()
            os.fsync(output.fileno())
        os._exit(23)
    journal.run_operation(task_id, 'crash-effect', 'file-write', {'dummy': 'input'}, apply, lambda _: True)


class TaskJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'profile'
        self.schema = json.loads((ROOT / 'config/phase2/profile.schema.json').read_text())
        self.files = {'config.json': (ROOT / 'config/phase2/profile/config.json').read_bytes()}
        self.profiles = ProfileStore(self.path, 'toddy-default', self.schema)
        self.revision = self.profiles.apply(self.files, expected_revision=None)
        self.now = 1000.0
        self.journal = TaskJournal(self.profiles, clock=lambda: self.now)
        self.task = self.journal.submit('request-1', self.revision, 'private dummy prompt')['task_id']

    def tearDown(self):
        self.temp.cleanup()

    def test_same_request_binding_across_reopen_and_profile_change(self):
        initial = self.journal.inspect(self.task)
        config = json.loads(self.files['config.json']); config['display_name'] = 'Changed'
        changed = self.profiles.apply({'config.json': json.dumps(config).encode()}, expected_revision=self.revision)
        reopened = TaskJournal(self.profiles)
        self.assertEqual(reopened.submit('request-1', self.revision, 'private dummy prompt'), initial)
        with self.assertRaisesRegex(TaskError, 'request_identity_conflict'):
            reopened.submit('request-1', changed, 'private dummy prompt')
        with self.assertRaisesRegex(TaskError, 'request_identity_conflict'):
            reopened.submit('request-1', self.revision, 'different prompt')
        self.assertEqual(self.profiles.task_snapshot(self.task), (self.revision, self.files))
        with self.profiles._db() as db:
            dump = '\n'.join(db.iterdump())
        self.assertNotIn('private dummy prompt', dump)

    def test_pure_accepted_lookup_is_exact_and_never_inserts(self):
        self.assertIsNone(self.journal.accepted_request('missing', self.revision, 'new text'))
        self.assertEqual(self.journal.accepted_request('request-1', self.revision, 'private dummy prompt')['task_id'], self.task)
        for metadata in ({'tool': 'changed'}, True):
            with self.assertRaisesRegex(TaskError, 'request_identity_conflict'):
                self.journal.accepted_request('request-1', self.revision, 'private dummy prompt', request_metadata=metadata)
        with self.profiles._db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM tasks').fetchone()[0], 1)

    def test_verified_effect_repeat_never_replays_and_sequences_increase(self):
        before = self.journal.inspect(self.task)['sequence']
        self.journal.start(self.task)
        calls = []
        def apply(*_):
            calls.append('effect'); return {'actual_postcondition': True, 'dummy-secret': 'private'}
        first = self.journal.run_operation(self.task, 'operation1', 'file-write', {'secret-input': 'dummy'}, apply,
                                           lambda result: result['actual_postcondition'])
        self.assertEqual(first['state'], 'completed')
        self.assertEqual(self.journal.run_operation(self.task, 'operation1', 'file-write', {'secret-input': 'dummy'},
                         lambda *_: self.fail('replay'), lambda _: True), first)
        self.assertEqual(calls, ['effect'])
        done = self.journal.complete(self.task)
        self.assertEqual(done['state'], 'completed'); self.assertGreater(done['sequence'], before)
        with self.profiles._db() as db:
            dump = '\n'.join(db.iterdump())
        for private in ('secret-input', 'dummy-secret', 'actual_postcondition'):
            self.assertNotIn(private, dump)

    def test_real_crash_effect_is_reconciled_read_only_without_duplicate(self):
        # Task was accepted with controlled clock; use a fresh real deadline.
        journal = TaskJournal(self.profiles)
        task_id = journal.submit('real-crash', self.revision, 'harmless synthetic')['task_id']
        journal.start(task_id)
        marker = Path(self.temp.name) / 'effect'
        child = multiprocessing.Process(target=lost_after_effect,
            args=(str(self.path), self.schema, task_id, str(marker)))
        child.start(); child.join(5)
        if child.is_alive():
            child.terminate(); child.join(5); self.fail('crash probe exceeded bound')
        self.assertEqual(child.exitcode, 23)
        self.assertEqual(marker.read_text(), 'effect-once')
        reopened = TaskJournal(self.profiles)
        self.assertGreater(reopened.recover(), 0)
        waiting = reopened.inspect(task_id)
        self.assertEqual(waiting['state'], 'waiting'); self.assertTrue(waiting['result_uncertain'])
        record = reopened.run_operation(task_id, 'crash-effect', 'file-write', {'dummy': 'input'},
                                       lambda *_: self.fail('replay after crash'), lambda _: True)
        self.assertEqual(record['state'], 'uncertain')
        inspected = []
        def check(operation_id, kind):
            inspected.append((operation_id, kind)); return marker.read_text() == 'effect-once'
        reopened.reconcile(task_id, 'crash-effect', check)
        self.assertEqual(inspected, [('crash-effect', 'file-write')])
        self.assertFalse(reopened.inspect(task_id)['result_uncertain'])
        self.assertEqual(reopened.complete(task_id)['state'], 'completed')
        self.assertEqual(marker.read_text(), 'effect-once')

    def test_unverified_or_exception_outcome_holds_and_stop_cannot_hide_uncertainty(self):
        self.journal.start(self.task)
        def apply(*_):
            raise OSError('dummy-secret-exception')
        with self.assertRaisesRegex(TaskError, 'operation_uncertain'):
            self.journal.run_operation(self.task, 'uncertain-op', 'file-write', {}, apply, lambda _: True)
        canceled = self.journal.cancel(self.task)
        self.assertEqual(canceled['state'], 'waiting'); self.assertTrue(canceled['result_uncertain'])
        for inspector in (lambda *_: False, lambda *_: {'looks-good': True}):
            self.assertEqual(self.journal.reconcile(self.task, 'uncertain-op', inspector)['state'], 'uncertain')
        with self.assertRaisesRegex(TaskError, 'task_not_completable'):
            self.journal.complete(self.task)
        with self.profiles._db() as db:
            self.assertNotIn('dummy-secret-exception', '\n'.join(db.iterdump()))
        self.journal.reconcile(self.task, 'uncertain-op', lambda *_: True)
        self.assertEqual(self.journal.inspect(self.task)['state'], 'canceled')
        self.assertEqual(self.journal.inspect(self.task)['summary'], 'stopped_after_verified_effect')

    def test_stop_before_dispatch_and_during_package_safe_boundary(self):
        self.assertEqual(self.journal.cancel(self.task)['state'], 'canceled')
        with self.assertRaisesRegex(TaskError, 'task_not_dispatchable'):
            self.journal.start(self.task)
        task = self.journal.submit('package-task', self.revision, 'synthetic package')['task_id']
        self.journal.start(task)
        began = threading.Event(); finish = threading.Event(); results = []
        def apply(*_):
            began.set()
            self.assertTrue(finish.wait(5))
            return True
        thread = threading.Thread(target=lambda: results.append(self.journal.run_operation(task, 'package-op', 'package',
                                  {}, apply, lambda output: output, boundary='package')))
        thread.start()
        try:
            self.assertTrue(began.wait(5))
            canceled = self.journal.cancel(task)
            self.assertEqual(canceled['state'], 'running')
            self.assertTrue(canceled['cancel_requested'])
            self.assertEqual(canceled['summary'], 'stop_pending_safe_boundary')
            with self.assertRaisesRegex(TaskError, 'task_dispatch_busy'):
                self.journal.recover()
            with self.assertRaisesRegex(TaskError, 'task_not_dispatchable'):
                self.journal.prepare_operation(task, 'forbidden-next', 'file-write', {})
        finally:
            finish.set(); thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(results[0]['state'], 'completed')
        final = self.journal.inspect(task)
        self.assertEqual(final['state'], 'canceled')
        self.assertEqual(final['summary'], 'stopped_after_verified_effect')
        self.assertFalse(final['result_uncertain'])

    def test_storage_and_deadline_refuse_before_effect(self):
        small = TaskJournal(self.profiles, clock=lambda: self.now, byte_limit=1)
        with self.assertRaisesRegex(TaskError, 'task_storage_full'):
            small.submit('new-full', self.revision, 'input')
        self.assertEqual(small.submit('request-1', self.revision, 'private dummy prompt')['task_id'], self.task)
        with self.assertRaisesRegex(TaskError, 'task_storage_full'):
            small.start(self.task)
        self.journal.start(self.task)
        with self.assertRaisesRegex(TaskError, 'task_storage_full'):
            small.run_operation(self.task, 'full-op', 'file-write', {}, lambda *_: self.fail(), lambda _: True)
        self.now += 301
        with self.assertRaisesRegex(TaskError, 'task_deadline'):
            self.journal.run_operation(self.task, 'expired-op', 'file-write', {}, lambda *_: self.fail(), lambda _: True)
        self.assertEqual(self.journal.cancel(self.task)['state'], 'canceled')

    def test_restart_holds_queued_and_prepared_and_never_restarts_worker(self):
        self.journal.start(self.task)
        self.journal.prepare_operation(self.task, 'prepared', 'file-write', {})
        queued = self.journal.submit('queued', self.revision, 'queued input')['task_id']
        self.assertEqual(self.journal.recover(), 2)
        self.assertEqual(self.journal.recover(), 0)
        for task in (self.task, queued):
            snapshot = self.journal.inspect(task)
            self.assertEqual(snapshot['state'], 'waiting')
            self.assertFalse(snapshot['result_uncertain'])
            self.assertEqual(snapshot['summary'], 'restart_review_required')
        with self.assertRaisesRegex(TaskError, 'task_not_dispatchable'):
            self.journal.start(self.task)
        with self.assertRaisesRegex(TaskError, 'task_not_dispatchable'):
            self.journal.run_operation(self.task, 'prepared', 'file-write', {}, lambda *_: self.fail('prepared replay'), lambda _: True)
        with self.assertRaisesRegex(TaskError, 'operation_not_reconcilable'):
            self.journal.reconcile(self.task, 'prepared', lambda *_: self.fail())

    def test_tool_budget_and_identity_conflict(self):
        self.journal.start(self.task)
        for count in range(8):
            self.journal.run_operation(self.task, 'op' + str(count), 'read-only', {}, lambda *_: True, lambda x: x)
        with self.assertRaisesRegex(TaskError, 'task_tool_limit'):
            self.journal.run_operation(self.task, 'too-many', 'read-only', {}, lambda *_: self.fail(), lambda _: True)
        with self.assertRaisesRegex(TaskError, 'operation_identity_conflict'):
            self.journal.run_operation(self.task, 'op0', 'read-only', {'changed': True}, lambda *_: self.fail(), lambda _: True)
        self.assertEqual(self.journal.complete(self.task)['state'], 'completed')


if __name__ == '__main__':
    unittest.main(verbosity=2)
