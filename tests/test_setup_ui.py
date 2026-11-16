"""Backend-independent setup model checks; GTK is exercised separately."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from runtime.setup.pending import SetupError
from runtime.ui.model import SetupModel, state_directory

ROOT = Path(__file__).resolve().parents[1]


class SetupModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'setup'
        self.model = SetupModel(ROOT, self.path, 'pt_BR.UTF-8')
        self.addCleanup(self.model.close)

    def test_backend_choice_is_nonsecret_intent_only_and_survives_reopen(self):
        self.model.choose_backend('api')
        with mock.patch.dict(os.environ, {}, clear=False):
            reopened = SetupModel(ROOT, self.path, 'en')
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.manifest['ai_choice'], 'api')
        self.assertEqual(reopened.manifest['consent_receipts'], [])
        self.assertNotIn('connection_ref', reopened.manifest)
        self.assertEqual(self.model.locale, 'pt-BR')
        self.assertEqual(reopened.locale, 'en')
        self.assertNotEqual(self.model.text('setup.title'), reopened.text('setup.title'))

    def test_configure_later_persists_dismissal_and_retains_deferred_wishes(self):
        self.model.manifest['choices'] = [{'id':'docker','artifact_id':None,
                                          'state':'deferred','error_code':'offline'}]
        self.model.choose_backend('local')
        self.model.defer()
        self.assertEqual(self.model.manifest['ai_choice'], 'later')
        self.assertTrue(self.model.manifest['invitation_dismissed'])
        self.assertEqual(self.model.manifest['choices'][0]['id'], 'docker')
        rows = self.model.software()
        self.assertTrue(next(r for r in rows if r['id']=='docker')['pending'])
        self.assertTrue(all(not row['can_install'] for row in rows))
        self.assertNotIn('git', {row['id'] for row in rows})

    def test_stale_ui_cannot_replace_another_ui_choice_and_reload_resolves(self):
        other = SetupModel(ROOT, self.path)
        self.addCleanup(other.close)
        other.choose_backend('local')
        with self.assertRaisesRegex(SetupError, 'stale_revision'):
            self.model.choose_backend('api')
        self.model.reload()
        self.assertEqual(self.model.manifest['ai_choice'], 'local')
        self.model.defer()
        other.reload()
        self.assertEqual(other.manifest['ai_choice'], 'later')

    def test_invalid_provider_mode_keeps_saved_manifest(self):
        before = copy.deepcopy(self.model.manifest)
        with self.assertRaisesRegex(SetupError, 'invalid_backend_choice'):
            self.model.choose_backend('cloud-required')
        self.model.reload()
        self.assertEqual(self.model.manifest, before)

    def test_relative_xdg_state_is_rejected(self):
        with mock.patch.dict(os.environ, {'XDG_STATE_HOME':'relative'}):
            with self.assertRaisesRegex(SetupError, 'state_directory'):
                state_directory()

class TaskProjectionTests(unittest.TestCase):
    def setUp(self):
        from runtime.ui.task_state import TaskState
        self.state = TaskState()
        self.state.begin_submit()
        self.state.submitted('task-example')

    def snapshot(self, sequence=1, **changes):
        import json
        data = {'version':1,'task_id':'task-example','profile_revision':'a'*64,
                'sequence':sequence,'state':'running','cancel_requested':False,
                'result_uncertain':False,'summary':'running','operation_id':None}
        data.update(changes)
        return json.dumps(data)

    def test_reconnect_keeps_existing_task_and_does_not_submit_another(self):
        self.state.observe(self.snapshot())
        self.state.disconnected()
        self.assertEqual(self.state.task_id, 'task-example')
        with self.assertRaisesRegex(ValueError, 'task_already_active'):
            self.state.begin_submit()
        self.state.observe(self.snapshot(2, state='completed'))
        self.assertEqual(self.state.snapshot['state'], 'completed')

    def test_disconnect_during_acceptance_holds_unknown_outcome(self):
        from runtime.ui.task_state import TaskState
        state = TaskState()
        state.begin_submit()
        state.disconnected()
        self.assertTrue(state.acceptance_uncertain)
        with self.assertRaisesRegex(ValueError, 'task_already_active'):
            state.begin_submit()

    def test_accepted_task_waiting_for_snapshot_and_uncertain_terminal_block_new_work(self):
        with self.assertRaisesRegex(ValueError, 'task_already_active'):
            self.state.begin_submit()
        self.state.observe(self.snapshot(state='failed',result_uncertain=True))
        with self.assertRaisesRegex(ValueError, 'task_already_active'):
            self.state.begin_submit()

    def test_snapshot_must_keep_the_submitted_profile_revision(self):
        self.state.profile_revision = 'b'*64
        with self.assertRaisesRegex(ValueError, 'invalid_snapshot'):
            self.state.observe(self.snapshot())
        self.assertIsNone(self.state.snapshot)

    def test_signal_gap_requires_snapshot_and_stale_sequence_is_discarded(self):
        self.state.observe(self.snapshot())
        self.assertEqual(self.state.observe(self.snapshot(3),signal=True),'gap')
        self.assertEqual(self.state.snapshot['sequence'],1)
        self.assertEqual(self.state.observe(self.snapshot(3)),'updated')
        self.assertEqual(self.state.observe(self.snapshot(2),signal=True),'stale')

    def test_wrong_task_malformed_state_or_unsafe_sequence_is_refused(self):
        for changes in ({'task_id':'other-task'},{'state':'invented'},
                        {'state':{}},{'sequence':True},{'sequence':2**53},
                        {'summary':'x'*4097},{'cancel_requested':'yes'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.state.observe(self.snapshot(**changes))
        self.assertIsNone(self.state.snapshot)

    def test_fixture_or_incomplete_capabilities_do_not_enable_task_dispatch(self):
        import json
        from runtime.ui.task_state import capabilities
        caps = {'version':1,'profile_id':'toddy-default','profile_revision':'b'*64,
                'features':['native-tools','durable-tasks','cancel'],'tools':['system-info'],
                'agent_backend':False}
        self.assertEqual(capabilities(json.dumps(caps))['agent_backend'],False)
        for change in ({'fixture_only':True},{'version':True},{'tools':[]},
                       {'features':[{}]},{'profile_revision':'guessed'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                capabilities(json.dumps(dict(caps,**change)))


class SetupBusSmokeTests(unittest.TestCase):
    def test_actual_async_client_reconnects_without_duplicate_submission(self):
        import importlib.util
        import json
        import shutil
        import subprocess
        import sys
        if importlib.util.find_spec('gi') is None or shutil.which('dbus-run-session') is None:
            self.skipTest('optional host GIO/session-bus unavailable; guest qualification still required')
        result = subprocess.run(['dbus-run-session','--',sys.executable,
            str(ROOT/'tests/fixtures/setup-client/smoke.py')],
            capture_output=True,text=True,timeout=15,cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        receipt=json.loads(result.stdout)
        self.assertEqual(receipt['status'],'passed')
        self.assertEqual(receipt['scope'],'host-actual-client-synthetic-service')
        self.assertEqual(receipt['counts']['SubmitTask'],1)
        self.assertEqual(receipt['counts']['RequestCancel'],1)
        self.assertEqual(receipt['counts']['GetTask'],2)


if __name__ == '__main__':
    unittest.main()
