"""Source-only GUI process/capture fixtures; no native root display acceptance."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from test_native_assistant_harness import h,c,manifest


class InstallerGuiPhaseTests(unittest.TestCase):
    def test_optional_phase_requires_actual_frozen_native_records(self):
        value=manifest();value['phases'].append('installer-gui')
        with self.assertRaisesRegex(ValueError,'missing_native_package'):h.validate_manifest(value)
        for name,version in h.INSTALLER_PACKAGES.items():
            row=copy.deepcopy(value['packages']['toddy-assistant']);row['version']=version
            row['record'].update(name=name,version=version);row['record_text']=json.dumps(row['record'])
            row['record_sha256']=hashlib.sha256(row['record_text'].encode()).hexdigest();value['packages'][name]=row
        self.assertEqual(h.validate_manifest(value)['phases'][-1],'installer-gui')
        value['packages']['qtbase']['version']='6.11.1'
        with self.assertRaisesRegex(ValueError,'installer_frozen'):h.validate_manifest(value)

    def test_preacceptance_probe_does_not_waive_B12_dependencies(self):
        status={'owner_review':{'phase_2_approved':True},'milestones':[{'id':key,'status':'completed','depends_on':[]} for key in ('B01','B02','B03')]+[
            {'id':'B12','status':'not_started','depends_on':['B06','B11']},{'id':'B06','status':'in_progress'},{'id':'B11','status':'not_started','depends_on':['B02','B06']}]}
        before=copy.deepcopy(status);self.assertTrue(c.phase_eligible('installer-gui',status));self.assertEqual(status,before)
        self.assertFalse(c.phase_eligible('branding',status))
        status['milestones'][0]['status']='in_progress';self.assertFalse(c.phase_eligible('installer-gui',status))
        status['owner_review']['phase_2_approved']=False;self.assertFalse(c.phase_eligible('installer-gui',status))

    def test_exact_config_has_no_execution_and_auto_target_query_fails_before_discovery(self):
        settings=(ROOT/'runtime/installer/calamares/settings.conf.in').read_bytes()
        show=settings.replace(b'- exec:\n  - toddy@review\n',b'').replace(b'- show:\n  - toddy@finished\n',b'')
        self.assertEqual(hashlib.sha256(show).hexdigest(),h.SHOW_ONLY_SHA256)
        self.assertNotIn(b'- exec:',show);self.assertIn(b'- show:\n  - toddy@review',show)
        cli=(ROOT/'runtime/installer/calamares/cli.py').read_text()
        self.assertLess(cli.index('adapter = CalamaresAdapter(create())'),cli.index('emit(targets(adapter))'))
        composition=(ROOT/'runtime/installer/composition.py').read_text()
        self.assertIn("BASE=Path('/usr/share/toddy/installer/composition')",composition)
        self.assertIn('self.recheck()',composition[composition.index('class Composition:'):])
        with patch.object(h.os.path,'lexists',return_value=True),patch.object(h,'sha') as digest:
            with self.assertRaisesRegex(ValueError,'composition_must_be_absent'):h.installer_gui_guard()
            digest.assert_not_called()
        with patch.object(h.os.path,'lexists',return_value=False),patch.object(h,'sha',return_value='wrong'),patch.object(h,'owned_regular') as native:
            with self.assertRaisesRegex(ValueError,'show_only_config_changed'):h.installer_gui_guard()
            native.assert_not_called()

    def test_actual_command_closed_environment_capture_and_owned_process_cleanup_fixture(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);runtime=root/'run/user'/str(h.UID);runtime.mkdir(parents=True)
            display=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);display.bind(str(runtime/'wayland-7'));self.addCleanup(display.close)
            proc=root/'proc/4242';proc.mkdir(parents=True);(proc/'status').write_text('Name:\tcalamares\nUid:\t0\t0\t0\t0\n')
            launch=ModuleType('toddy.installer.launch');launch.qualification_command=Mock(return_value=(['/usr/bin/calamares','-c','/usr/share/toddy/installer/calamares-qualification'],{'LANG':'en_US.UTF-8'}))
            child=Mock(pid=4242);child.poll.return_value=None
            channel=Mock();channel.readline.return_value=b'INPUT-ACK\n'
            def path(value):return root/str(value).lstrip('/')
            with patch.dict(sys.modules,{'toddy.installer.launch':launch}),patch.object(h,'installer_gui_guard'),patch.object(h,'Path',side_effect=path),\
                    patch.object(h.subprocess,'check_output',return_value="'default'"),patch.object(h.subprocess,'Popen',return_value=child) as spawn,\
                    patch.object(h.time,'sleep'),patch.object(h.select,'select',return_value=([channel],[],[])):
                result=h.installer_gui({'fixture_only':True},channel)
                self.assertEqual(spawn.call_count,4);self.assertEqual(child.terminate.call_count,4);self.assertEqual(child.wait.call_count,4)
                self.assertEqual(launch.qualification_command.call_args_list[0].args,(h.UID,'wayland-7','en_US.UTF-8'))
                self.assertEqual(launch.qualification_command.call_args_list[-1].args,(h.UID,'wayland-7','pt_BR.UTF-8'))
                self.assertTrue(result['visual_review_required']);self.assertFalse(result['B12_acceptance']);self.assertFalse(result['launch_qualification_receipt_written'])
                self.assertEqual(len(result['cases']),4);self.assertTrue(all(row['actual_root_GUI_reaped'] for row in result['cases']))
                self.assertTrue(all(call.kwargs['close_fds'] for call in spawn.call_args_list))
                self.assertTrue(all(b'capture' in call.args[0] or b'tab' in call.args[0] for call in channel.write.call_args_list))

    def test_root_phase_bypasses_user_client_and_broker_calls(self):
        source=(ROOT/'scripts/host/phase2-native-assistant-hook.py').read_text();tree=ast.parse(source)
        main=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='main')
        gate=next(node for node in ast.walk(main) if isinstance(node,ast.If) and ast.unparse(node.test)=="phase == 'installer-gui'")
        self.assertIn('installer_gui',ast.unparse(gate.body));self.assertNotIn('subprocess.run',ast.unparse(gate.body))
        self.assertIn('subprocess.run',ast.unparse(gate.orelse))

if __name__=='__main__':unittest.main()
