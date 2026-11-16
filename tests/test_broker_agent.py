"""Trusted engine callback orchestration and canonical effects/output; synthetic model."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime/broker'))
from profiles import ProfileStore
from tasks import TaskJournal, TaskError
from text import TaskText
from core import BrokerCore, BrokerError, NATIVE_TOOLS


@unittest.skipIf(os.geteuid() == 0, 'broker deliberately refuses root')
class BrokerAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.workspace = self.directory / 'workspace'; self.workspace.mkdir(mode=0o700)
        schema = json.loads((ROOT / 'config/phase2/profile.schema.json').read_text())
        self.config = json.loads((ROOT / 'config/phase2/profile/config.json').read_text())
        self.config['provider'] = {'mode': 'local', 'adapter_id': 'local-llama-cpp',
            'model_id': 'synthetic-only', 'connection_ref': 'local-test', 'allow_remote_fallback': False}
        self.config['tools']['enabled'] = ['file-write']
        self.profiles = ProfileStore(self.directory / 'profile', 'toddy-default', schema,
            capabilities={'adapters': {'local-llama-cpp', 'openai'}, 'tools': NATIVE_TOOLS, 'skills': {'explain-system'}})
        self.revision = self.profiles.apply({'config.json': json.dumps(self.config).encode()}, expected_revision=None)
        self.journal = TaskJournal(self.profiles)
        self.text = TaskText(self.journal)
        self.calls = []
        parent = self
        class Engine:
            @staticmethod
            def available(_):
                return True
            def __call__(self, files, revision, task, prompt, consent, on_tool, on_text, canceled):
                parent.calls.append((revision, task, consent))
                result = on_tool('tool-1', 'file-write', {'path': 'actual.txt', 'text': 'once', 'expected_sha256': None})
                parent.assertEqual(result['outcome'], 'verified')
                on_text('Verified actual file content once.')
                return {'state': 'completed'}
        self.core = BrokerCore(self.profiles, self.journal, self.workspace, engine_runner=Engine(), text_store=self.text,
                               dispatch_allowed=lambda: True)

    def tearDown(self):
        self.temp.cleanup()

    def body(self, **changes):
        body = {'version': 1, 'agent': True, 'text': 'Synthetic agent orchestration', 'remote_consent': False}
        body.update(changes)
        return json.dumps(body)

    def test_actual_workspace_effect_and_private_text_are_separately_durable_and_deduped(self):
        snapshot, request = self.core.submit('agent-one', self.revision, self.body())
        done = self.core.execute(snapshot['task_id'], request)
        self.assertEqual(done['state'], 'completed'); self.assertFalse(done['result_uncertain'])
        self.assertEqual((self.workspace / 'actual.txt').read_text(), 'once')
        page = self.text.page(snapshot['task_id'], 0)
        self.assertTrue(page['complete'])
        self.assertEqual(''.join(chunk['text'] for chunk in page['chunks']), 'Verified actual file content once.')
        self.assertNotIn('Verified actual', json.dumps(done))
        duplicate, same = self.core.submit('agent-one', self.revision, self.body())
        self.assertEqual(self.core.execute(duplicate['task_id'], same), done)
        self.assertEqual(len(self.calls), 1)
        with self.journal.profiles._db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM task_operations').fetchone()[0], 1)

    def test_worker_completed_cannot_hide_an_unverified_native_effect(self):
        core = self.core
        class Engine:
            def __call__(self, _files, _revision, _task, _prompt, _consent, on_tool, _on_text, _canceled):
                # A second write using a wrong precondition has unknown outcome
                # at the independent adapter boundary; never trust done alone.
                result = on_tool('tool-1', 'file-write', {'path': 'missing-dir/actual.txt', 'text': 'never', 'expected_sha256': None})
                self.result = result
                return {'state': 'completed'}
        engine = Engine(); core.engine_runner = engine
        snapshot, request = core.submit('uncertain', self.revision, self.body())
        with self.assertRaisesRegex(TaskError, 'task_not_completable'):
            core.execute(snapshot['task_id'], request)
        self.assertEqual(engine.result['outcome'], 'uncertain')
        self.assertEqual(core.journal.inspect(snapshot['task_id'])['state'], 'waiting')
        self.assertTrue(core.journal.inspect(snapshot['task_id'])['result_uncertain'])
        self.assertTrue(self.text.page(snapshot['task_id'], 0)['complete'])
        self.assertFalse((self.workspace / 'missing-dir').exists())

    def test_remote_consent_is_per_request_and_profile_tool_checks_remain_independent(self):
        with self.assertRaisesRegex(BrokerError, 'local_remote_consent_mismatch'):
            self.core.submit('bad-remote', self.revision, self.body(remote_consent=True))
        self.config['provider']['mode'] = 'remote'
        self.config['provider']['adapter_id'] = 'openai'
        self.config['budgets']['remote_spending_enabled'] = True
        self.revision = self.profiles.apply({'config.json': json.dumps(self.config).encode()}, expected_revision=self.revision)
        with self.assertRaisesRegex(BrokerError, 'remote_consent_required'):
            self.core.submit('no-consent', self.revision, self.body())
        # Merely configuring spending or importing a provider grants no per-task consent.
        with self.journal.profiles._db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM tasks').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
