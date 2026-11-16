"""Source contracts only; no GTK, systemd, model, keyring or VM acceptance."""
import ast,importlib.util,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('offline_setup_hook',ROOT/'scripts/host/phase2-native-assistant-hook.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)


class OfflineSetupTests(unittest.TestCase):
    def test_offline_client_branch_precedes_every_broker_capability_call(self):
        tree=ast.parse(h.USER_CLIENT);compile(tree,'unqualified-native-client-source','exec')
        guarded=next(node for node in tree.body if isinstance(node,ast.If) and ast.unparse(node.test)=="phase != 'setup-offline'")
        calls=[node for node in ast.walk(guarded) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='call']
        self.assertTrue(calls)
        for node in tree.body:
            if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name):self.assertNotEqual(node.value.func.id,'call')
        branch=next(node for node in tree.body if isinstance(node,ast.If) and ast.unparse(node.test)=="phase == 'setup-offline'")
        source=ast.unparse(branch.body)
        self.assertIn('get_component_iface().grab_focus()',source)
        self.assertIn("'actual_QMP_acknowledged': True",source)
        self.assertIn("'setup.save_intent'",source)
        self.assertIn('PendingStore',source);self.assertIn('NameHasOwner',source)
        self.assertNotIn("call('GetCapabilities'",source)

    def test_runtime_mask_and_prior_activity_restored_with_fixed_owned_user_commands(self):
        env={'PATH':'/usr/bin:/usr/sbin','DBUS_SESSION_BUS_ADDRESS':'UNQUALIFIED FIXTURE'}
        responses=['disabled','inactive','','masked-runtime','0','','','inactive','disabled']
        commands=[]
        def run(argv,**kwargs):
            commands.append(argv)
            self.assertEqual(kwargs['user'],h.UID);self.assertEqual(kwargs['group'],h.UID)
            self.assertEqual(kwargs['extra_groups'],[]);self.assertEqual(kwargs['env'],env)
            return subprocess.CompletedProcess(argv,0,responses.pop(0),'')
        with patch.object(h.subprocess,'run',side_effect=run):
            prior=h.offline_user_service(env,'mask');self.assertEqual(prior,{'enabled':'disabled','active':False})
            self.assertTrue(h.offline_user_service(env,'restore',prior)['restored'])
        self.assertIn(['/usr/bin/systemctl','--user','mask','--runtime','--now','toddy-agent.service'],commands)
        self.assertIn(['/usr/bin/systemctl','--user','unmask','--runtime','toddy-agent.service'],commands)
        self.assertNotIn(['/usr/bin/systemctl','--user','start','toddy-agent.service'],commands)

    def test_existing_mask_and_unsettled_service_refused_before_suppression(self):
        for replies in (['masked-runtime'],['disabled','activating']):
            calls=[]
            def run(argv,**kwargs):calls.append(argv);return subprocess.CompletedProcess(argv,0,replies.pop(0),'')
            with patch.object(h.subprocess,'run',side_effect=run),self.assertRaises(ValueError):h.offline_user_service({},'mask')
            self.assertFalse(any('mask' in argv for argv in calls))


if __name__=='__main__':unittest.main()
