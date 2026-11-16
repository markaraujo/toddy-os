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
        for change in ({'fixture_only':True},{'version':True},{'tools':[{}]},
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





class ConversationTextTests(unittest.TestCase):
    def page(self,after=0,*,complete=True,latest=2):
        import json
        rows=[{'sequence':1,'text':'<b>Literal text</b> '},{'sequence':2,'text':'Olá.'}]
        chunks=[row for row in rows if row['sequence']>after][:1]
        return json.dumps({'version':1,'task_id':'task-example','chunks':chunks,
                           'next_sequence':chunks[-1]['sequence'] if chunks else after,
                           'latest_sequence':latest,'complete':complete,'history_enabled':False})

    def test_finalized_text_can_need_more_pages_and_remains_plain_untrusted_text(self):
        from runtime.ui.task_state import TaskText
        text=TaskText('task-example')
        self.assertTrue(text.observe(self.page()))
        self.assertTrue(text.complete)
        self.assertFalse(text.observe(self.page(1)))
        self.assertEqual(text.text,'<b>Literal text</b> Olá.')
        self.assertEqual(text.sequence,2)
        self.assertFalse(text.history_enabled)
        self.assertFalse(text.observe(self.page(2)))
        self.assertEqual(text.text,'<b>Literal text</b> Olá.')

    def test_bad_text_page_does_not_advance_cursor_or_append_partial_content(self):
        import json
        from runtime.ui.task_state import TaskText
        for change in [{'task_id':'other'},{'next_sequence':True},
                       {'chunks':[{'sequence':2,'text':'skip'}]},
                       {'chunks':[]},{'chunks':[{'sequence':1,'text':'x'*1025}]}]:
            value=json.loads(self.page());value.update(change)
            text=TaskText('task-example')
            with self.subTest(change=change),self.assertRaises(ValueError):
                text.observe(json.dumps(value))
            self.assertEqual(text.sequence,0)
            self.assertEqual(text.text,'')

    def test_conversation_profile_stop_and_reconnect_use_negotiated_service_extensions(self):
        import importlib.util
        import json
        import shutil
        import subprocess
        import sys
        if importlib.util.find_spec('gi') is None or shutil.which('dbus-run-session') is None:
            self.skipTest('optional host GIO/session-bus unavailable; native qualification remains required')
        result=subprocess.run(['dbus-run-session','--',sys.executable,
            str(ROOT/'tests/fixtures/setup-client/conversation.py')],
            capture_output=True,text=True,timeout=15,cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        receipt=json.loads(result.stdout)
        self.assertEqual(receipt['status'],'passed')
        self.assertEqual(receipt['scope'],'host-actual-client-synthetic-service')
        self.assertEqual(receipt['counts']['SubmitTask'],1)
        self.assertEqual(receipt['counts']['RequestCancel'],1)
        self.assertEqual(receipt['counts']['ValidateProfile'],2)
        self.assertEqual(receipt['counts']['ApplyProfile'],1)
        self.assertEqual(receipt['counts']['RestoreProfile'],1)
        self.assertEqual(receipt['counts']['GetTaskText'],2)
        self.assertEqual(receipt['counts']['AcknowledgeTaskText'],1)





class AsyncClientPolicyTests(unittest.TestCase):
    def client(self):
        import importlib.util
        if importlib.util.find_spec('gi') is None:
            self.skipTest('optional GIO unavailable')
        from runtime.ui.bridge import TaskClient
        from runtime.ui.task_state import TaskState
        client=TaskClient.__new__(TaskClient)
        client.phase='ready'
        client.state=TaskState()
        client.capabilities={'features':['agent-text-v1','profile-settings-v1'],
            'profile_id':'toddy-default','profile_revision':'a'*64,
            'agent_backend':True,'provider_mode':'remote'}
        return client

    def test_remote_request_needs_current_explicit_consent_and_local_never_reuses_it(self):
        from unittest import mock
        client=self.client()
        client._submit=mock.Mock()
        with self.assertRaisesRegex(ValueError,'remote_consent_required'):
            client.submit_text('Question',remote_consent=False)
        client._submit.assert_not_called()
        client.submit_text('Question',remote_consent=True)
        self.assertTrue(client._submit.call_args.args[1]['remote_consent'])
        client.capabilities['provider_mode']='local'
        client.submit_text('Local question',remote_consent=True)
        self.assertFalse(client._submit.call_args.args[1]['remote_consent'])

    def test_edit_after_validation_dispatch_invalidates_its_late_reply(self):
        import json
        client=self.client()
        client.profile={'profile_revision':'a'*64}
        client.profile_stage=None
        client.profile_status='loaded'
        client.profile_edit_generation=0
        calls=[]
        client._call=lambda *args:calls.append(args)
        client.validate_profile('{}')
        client.invalidate_profile_stage()
        calls[0][2](json.dumps({'version':1,'valid':True,'validated_revision':'stage-old',
                               'profile_revision':'b'*64}))
        self.assertIsNone(client.profile_stage)
        self.assertEqual(client.profile_status,'editing')

    def test_old_task_text_reply_cannot_clear_a_new_task_fetch_or_append_text(self):
        import json
        from runtime.ui.task_state import TaskText
        client=self.client()
        client.state.task_id='old-task'
        client.text=None
        client.text_generation=1
        client.text_fetching=False
        client.text_dirty=False
        calls=[]
        client._call=lambda *args:calls.append(args)
        client.refresh_text()
        client.state.task_id='new-task'
        client.text=TaskText('new-task')
        client.text_generation=2
        client.text_fetching=True
        calls[0][2](json.dumps({'version':1,'task_id':'old-task','chunks':[],
                               'next_sequence':0,'latest_sequence':0,
                               'complete':True,'history_enabled':False}))
        self.assertTrue(client.text_fetching)
        self.assertEqual(client.text.task_id,'new-task')
        self.assertEqual(client.text.text,'')


if __name__ == '__main__':unittest.main()
