"""Actual canonical SQLite output paging, limits, retention and interrupted runs."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime/broker'))
from profiles import ProfileStore
from tasks import TaskJournal
from text import TaskText, TextError


class TaskTextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'profile'
        self.schema = json.loads((ROOT / 'config/phase2/profile.schema.json').read_text())
        self.profiles = ProfileStore(self.path, 'toddy-default', self.schema)
        self.revision = self.profiles.apply({'config.json': (ROOT / 'config/phase2/profile/config.json').read_bytes()}, expected_revision=None)
        self.journal = TaskJournal(self.profiles)
        self.task = self.journal.submit('text-request', self.revision, 'private prompt not output')['task_id']
        self.now = 1000.
        self.text = TaskText(self.journal, clock=lambda: self.now)
        self.text.begin(self.task, history_enabled=False, retention_days=0)

    def tearDown(self):
        self.temp.cleanup()

    def test_utf8_private_pages_bound_encoded_bytes_and_drain_finalized_long_output(self):
        original = ('🐶\0line\n' * 11000)[:75000]
        self.text.append(self.task, original)
        self.text.finish(self.task)
        result, cursor, pages = [], 0, 0
        while True:
            page = self.text.page(self.task, cursor)
            self.assertLessEqual(len(json.dumps(page, ensure_ascii=False, separators=(',', ':')).encode()), 32768)
            self.assertTrue(page['complete']); self.assertFalse(page['history_enabled'])
            for chunk in page['chunks']:
                self.assertLessEqual(len(chunk['text'].encode()), 1024)
                self.assertEqual(chunk['sequence'], cursor + 1)
                cursor = chunk['sequence']; result.append(chunk['text'])
            self.assertEqual(page['next_sequence'], cursor)
            pages += 1
            if cursor >= page['latest_sequence']:
                break
            self.assertTrue(page['chunks'])
        self.assertGreater(pages, 1); self.assertEqual(''.join(result), original)
        reopened = TaskText(TaskJournal(ProfileStore(self.path, 'toddy-default', self.schema)), clock=lambda: self.now)
        self.assertEqual(reopened.page(self.task, 0)['chunks'], self.text.page(self.task, 0)['chunks'])
        with self.profiles._db() as db:
            row = dict(db.execute('SELECT * FROM tasks WHERE id=?', (self.task,)).fetchone())
        self.assertNotIn('🐶', json.dumps(row, ensure_ascii=False)); self.assertNotIn('private prompt not output', json.dumps(row))

    def test_history_off_transient_expiry_keeps_indispensable_task_metadata(self):
        self.text.append(self.task, 'Private assistant output.')
        self.text.finish(self.task)
        self.now += 301
        with self.assertRaisesRegex(TextError, 'task_text_unavailable'):
            self.text.page(self.task, 0)
        self.assertEqual(self.text.purge_expired(), 1)
        self.assertEqual(self.text.purge_expired(), 0)
        self.assertEqual(self.journal.inspect(self.task)['task_id'], self.task)
        with self.profiles._db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM task_text_chunks').fetchone()[0], 0)

    def test_limits_invalid_cursors_and_finalized_store_do_not_truncate_prior_output(self):
        small = TaskText(self.journal, task_limit=10)
        small.append(self.task, 'keep')
        with self.assertRaisesRegex(TextError, 'task_text_limit'):
            small.append(self.task, 'way too much output')
        self.assertEqual(small.page(self.task, 0)['chunks'][0]['text'], 'keep')
        for cursor in (True, -1, 999, 2**53):
            with self.assertRaisesRegex(TextError, 'invalid_text_cursor'):
                small.page(self.task, cursor)
        small.finish(self.task)
        with self.assertRaisesRegex(TextError, 'task_text_not_writable'):
            small.append(self.task, 'bad')

    def test_acknowledgement_erases_transient_data_only_after_complete_drain(self):
        sequence = self.text.append(self.task, 'Current response only.')
        with self.assertRaisesRegex(TextError, 'text_ack_incomplete'):
            self.text.acknowledge(self.task, sequence)
        self.text.finish(self.task)
        with self.assertRaisesRegex(TextError, 'text_ack_incomplete'):
            self.text.acknowledge(self.task, 0)
        self.assertTrue(self.text.acknowledge(self.task, sequence)['erased'])
        self.assertTrue(self.text.acknowledge(self.task, sequence)['erased'])
        with self.assertRaisesRegex(TextError, 'task_text_unavailable'):
            self.text.page(self.task, 0)
        self.assertEqual(self.journal.inspect(self.task)['task_id'], self.task)

    def test_configured_history_retention_is_separate_and_transient_restart_is_erased(self):
        history = self.journal.submit('history-task', self.revision, 'another private prompt')['task_id']
        self.text.begin(history, history_enabled=True, retention_days=2)
        latest = self.text.append(history, 'Explicit retained response.')
        self.text.finish(history)
        self.assertFalse(self.text.acknowledge(history, latest)['erased'])
        self.text.append(self.task, 'Interrupted transient response.')
        self.text.recover()
        self.assertEqual(self.text.purge_transient(), 1)
        self.assertEqual(self.text.purge_transient(), 0)
        with self.assertRaisesRegex(TextError, 'task_text_unavailable'):
            self.text.page(self.task, 0)
        self.now += 86400
        self.assertTrue(self.text.page(history, 0)['history_enabled'])
        self.now += 86401
        self.assertEqual(self.text.purge_expired(), 1)

    def test_recovery_finalizes_partial_output_without_task_or_model_replay(self):
        self.text.append(self.task, 'Interrupted actual response.')
        self.assertFalse(self.text.page(self.task, 0)['complete'])
        self.assertEqual(self.text.recover(), 1)
        self.assertEqual(self.text.recover(), 0)
        self.assertTrue(self.text.page(self.task, 0)['complete'])
        self.assertEqual(self.journal.inspect(self.task)['state'], 'queued')
        self.assertEqual(self.journal.recover(), 1)
        self.assertEqual(self.journal.inspect(self.task)['state'], 'waiting')


if __name__ == '__main__':
    unittest.main(verbosity=2)
