"""Actual unprivileged workspace effects routed through the durable native core."""
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
from core import BrokerCore, BrokerError, NATIVE_TOOLS


@unittest.skipIf(os.geteuid() == 0, 'ordinary tools deliberately refuse root')
class BrokerCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.workspace = root / 'workspace'; self.workspace.mkdir(mode=0o700)
        self.schema = json.loads((ROOT / 'config/phase2/profile.schema.json').read_text())
        self.config = json.loads((ROOT / 'config/phase2/profile/config.json').read_text())
        self.profiles = ProfileStore(root / 'profile', 'toddy-default', self.schema,
            capabilities={'adapters': set(), 'tools': NATIVE_TOOLS, 'skills': {'explain-system'}})
        self.revision = self.profiles.apply({'config.json': json.dumps(self.config).encode()}, expected_revision=None)
        self.journal = TaskJournal(self.profiles)
        self.allowed = True
        self.core = BrokerCore(self.profiles, self.journal, self.workspace, dispatch_allowed=lambda: self.allowed)

    def tearDown(self):
        self.temp.cleanup()

    def body(self, kind='system-info', arguments=None):
        return json.dumps({'version': 1, 'text': 'Owner native action',
                           'tool': {'kind': kind, 'arguments': arguments or {}}})

    def enable(self, tools):
        self.config['tools']['enabled'] = tools
        self.revision = self.profiles.apply({'config.json': json.dumps(self.config).encode()}, expected_revision=self.revision)

    def test_actual_system_info_task_and_disabled_backend(self):
        cap = self.core.capabilities()
        self.assertFalse(cap['agent_backend']); self.assertEqual(cap['tools'], ['system-info'])
        snapshot, request = self.core.submit('system1', self.revision, self.body())
        result = self.core.execute(snapshot['task_id'], request)
        self.assertEqual(result['state'], 'completed'); self.assertFalse(result['result_uncertain'])
        again, same_request = self.core.submit('system1', self.revision, self.body())
        self.assertEqual(again['task_id'], snapshot['task_id'])
        self.assertEqual(self.core.execute(again['task_id'], same_request), result)

    def test_actual_workspace_write_hash_guard_and_pinned_selection(self):
        self.enable(['file-write', 'file-read'])
        snapshot, request = self.core.submit('write1', self.revision,
            self.body('file-write', {'path': 'hello.txt', 'text': 'Hello, Toddy!', 'expected_sha256': None}))
        # Disable tools for new tasks after acceptance; this task keeps its pin.
        self.enable(['system-info'])
        result = self.core.execute(snapshot['task_id'], request)
        self.assertEqual(result['state'], 'completed')
        self.assertEqual((self.workspace / 'hello.txt').read_text(), 'Hello, Toddy!')
        self.assertEqual(self.core.execute(snapshot['task_id'], request), result)
        with self.assertRaisesRegex(BrokerError, 'profile_tool_disabled'):
            self.core.submit('write-disabled', self.revision,
                self.body('file-write', {'path': 'hello.txt', 'text': 'bad', 'expected_sha256': None}))

    def test_locked_session_and_stop_before_effect(self):
        self.allowed = False
        with self.assertRaisesRegex(BrokerError, 'interactive_session_unavailable'):
            self.core.submit('locked', self.revision, self.body())
        self.allowed = True
        snapshot, request = self.core.submit('accepted', self.revision, self.body())
        self.allowed = False
        with self.assertRaisesRegex(BrokerError, 'interactive_session_unavailable'):
            self.core.execute(snapshot['task_id'], request)
        self.assertEqual(self.journal.inspect(snapshot['task_id'])['state'], 'canceled')

    def test_root_routing_uses_client_not_profile_authority(self):
        self.enable(['admin-config'])
        snapshot, request = self.core.submit('root-unavailable', self.revision,
            self.body('admin-config', {'path': '/etc/dummy', 'text': 'no write', 'expected_sha256': None}))
        with self.assertRaisesRegex(TaskError, 'operation_uncertain'):
            self.core.execute(snapshot['task_id'], request)
        self.assertTrue(self.journal.inspect(snapshot['task_id'])['result_uncertain'])
        called = []
        class Client:
            def dispatch(self, op, kind, args, canceled):
                called.append((op, kind, args, canceled())); return {'verified': True}
            def cancel(self, op):
                called.append(('cancel', op))
        self.core.root_client = Client()
        snapshot, request = self.core.submit('root-adapter-fixture', self.revision,
            self.body('admin-config', {'path': '/etc/dummy', 'text': 'adapter only', 'expected_sha256': None}))
        self.assertEqual(self.core.execute(snapshot['task_id'], request)['state'], 'completed')
        self.assertEqual(called[0][1], 'config_replace')
        self.assertFalse(called[0][3])
        # No root filesystem operation occurs in this adapter-only test.

    def test_root_effect_reconciliation_only_inspects_without_dispatch(self):
        self.enable(['admin-config'])
        snapshot, request = self.core.submit('root-crash', self.revision,
            self.body('admin-config', {'path': '/etc/dummy', 'text': 'never written by fixture', 'expected_sha256': None}))
        with self.assertRaisesRegex(TaskError, 'operation_uncertain'):
            self.core.execute(snapshot['task_id'], request)
        inspections = []
        class Client:
            def inspect(self, op):
                inspections.append(op)
                return {'state': 'completed', 'result': {'verified': True}}
            def dispatch(self, *_):
                raise AssertionError('reconciliation must not dispatch')
        self.core.root_client = Client()
        reconciled = self.core.reconcile(snapshot['task_id'])
        self.assertEqual(reconciled['state'], 'completed')
        self.assertFalse(reconciled['result_uncertain'])
        self.assertEqual(inspections, [snapshot['operation_id'] or reconciled['operation_id']])

    def test_request_tool_arguments_are_part_of_dedup_and_invalid_input_refused(self):
        self.enable(['file-write'])
        first = self.body('file-write', {'path': 'file', 'text': 'first', 'expected_sha256': None})
        changed = self.body('file-write', {'path': 'file', 'text': 'changed', 'expected_sha256': None})
        self.core.submit('identity', self.revision, first)
        with self.assertRaisesRegex(TaskError, 'request_identity_conflict'):
            self.core.submit('identity', self.revision, changed)
        for invalid in ('{"version":1,"version":1}', self.body('file-write', {'path': 'bad'})):
            with self.assertRaises(BrokerError):
                self.core.submit('invalid', self.revision, invalid)


if __name__ == '__main__':
    unittest.main(verbosity=2)
