"""Temporary-tree write evidence only; no guest/package/model acceptance."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/build/phase2'))
import voice_native as voice


class WriteAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.base=Path(self.temporary.name);self.target=self.base/'target';self.target.mkdir()
        for name in ('usr','etc','var','boot'):(self.target/name).mkdir()
        (self.target/'usr/existing').write_text('before');(self.target/'etc/removed').write_text('old')
        self.prefix=self.base/'voice-fixture';self.lock=self.base/'build.lock'
        self.lease=self.lock.open('a');self.addCleanup(self.lease.close)
        fcntl.flock(self.lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        self.pins={'fixture_source_only':'a'*64}
        for patched in (patch.object(voice,'T',self.target),patch.object(voice,'BUILD_LOCK',self.lock),
                        patch.object(voice.root_audit,'TARGET',self.target),patch.object(voice,'audit_pins',return_value=self.pins)):
            patched.start();self.addCleanup(patched.stop)
        self.command=[sys.executable,'-c',"from pathlib import Path;import sys;p=Path(sys.argv[1]);(p/'usr/existing').write_text('after');(p/'etc/removed').unlink();(p/'boot/new').write_text('fixture')",str(self.target)]
        self.inputs={'scope':'Temporary source test only; never native acceptance','source_sha256':'b'*64}
    def path(self,suffix):return voice.audit_path(self.prefix,'install',suffix)
    def successful_fixture(self):
        with voice.native_write_audit(self.prefix,'install',self.command,self.inputs,self.lease) as audit:
            self.assertTrue((self.base/'voice-fixture.install-audit.running.json').exists())
            actual=subprocess.run(self.command,check=True,capture_output=True)
            audit['command_exit']=actual.returncode
            self.assertEqual((self.target/'boot/new').read_text(),'fixture')
            audit['postcheck_exit']=0;audit['package_record_sha256']='c'*64
        return voice.require_write_audit(self.prefix,'install',inputs=self.inputs,command=self.command,record_sha256='c'*64)
    def test_full_before_after_add_modify_remove_and_same_lock_remains_owned(self):
        terminal=self.successful_fixture();self.assertEqual(terminal,voice.digest(self.path('complete.json')))
        changes=json.loads(self.path('manifest.json').read_text())
        self.assertEqual(set(changes),{'/usr/existing','/etc/removed','/boot/new'})
        self.assertIsNone(changes['/etc/removed']['after']);self.assertIsNone(changes['/boot/new']['before'])
        self.assertNotEqual(changes['/usr/existing']['before']['sha256'],changes['/usr/existing']['after']['sha256'])
        with self.lock.open('a') as independent:
            with self.assertRaises(BlockingIOError):fcntl.flock(independent,fcntl.LOCK_EX|fcntl.LOCK_NB)
        self.assertFalse(self.path('failed.json').exists());self.assertFalse((self.base/'voice-fixture.install-audit.running.json').exists())
    def test_actual_failed_child_exit_keeps_mutation_manifest_and_refuses_replay(self):
        command=[sys.executable,'-c',"from pathlib import Path;import sys;(Path(sys.argv[1])/'usr/partial').write_text('partial');sys.exit(7)",str(self.target)]
        with self.assertRaises(subprocess.CalledProcessError):
            with voice.native_write_audit(self.prefix,'install',command,self.inputs,self.lease):subprocess.run(command,check=True,capture_output=True)
        row=json.loads(self.path('failed.json').read_text());self.assertEqual(row['command_exit'],7);self.assertIsNone(row['postcheck_exit'])
        self.assertIn('/usr/partial',json.loads(self.path('manifest.json').read_text()))
        self.assertFalse(self.path('complete.json').exists())
        with self.assertRaisesRegex(ValueError,'exists_inspect_no_replay'):
            with voice.native_write_audit(self.prefix,'install',command,self.inputs,self.lease):self.fail('uncertain operation replayed')
    def test_postcheck_failure_does_not_replace_actual_successful_command_exit(self):
        with self.assertRaises(subprocess.CalledProcessError):
            with voice.native_write_audit(self.prefix,'install',self.command,self.inputs,self.lease) as audit:
                audit['command_exit']=subprocess.run(self.command,check=True,capture_output=True).returncode
                subprocess.run([sys.executable,'-c','raise SystemExit(9)'],check=True,capture_output=True)
        row=json.loads(self.path('failed.json').read_text());self.assertEqual((row['command_exit'],row['postcheck_exit']),(0,9))
    def test_missing_postcheck_and_boolean_exit_never_become_success(self):
        with self.assertRaisesRegex(ValueError,'postconditions_incomplete'):
            with voice.native_write_audit(self.prefix,'install',self.command,self.inputs,self.lease) as audit:audit['command_exit']=False
        self.assertFalse(self.path('complete.json').exists());self.assertEqual(json.loads(self.path('failed.json').read_text())['state'],'failed')
    def test_snapshot_failure_retains_intent_without_false_terminal_success(self):
        before=voice.root_audit.snapshot()
        with patch.object(voice.root_audit,'snapshot',side_effect=[before,OSError('fixture scan failure')]):
            with self.assertRaises(OSError):
                with voice.native_write_audit(self.prefix,'install',self.command,self.inputs,self.lease) as audit:
                    audit.update(command_exit=0,postcheck_exit=0)
        self.assertTrue((self.base/'voice-fixture.install-audit.running.json').exists())
        self.assertTrue(self.path('intent.json').exists());self.assertTrue(self.path('before.json').exists());self.assertFalse(self.path('complete.json').exists())
        with self.assertRaises(FileNotFoundError):voice.require_write_audit(self.prefix,'install')
    def test_evidence_command_source_and_package_record_changes_are_rejected(self):
        self.successful_fixture()
        with self.assertRaisesRegex(ValueError,'command_changed'):voice.require_write_audit(self.prefix,'install',command=['another command'])
        with self.assertRaisesRegex(ValueError,'inputs_changed'):voice.require_write_audit(self.prefix,'install',inputs={'changed':True})
        with self.assertRaisesRegex(ValueError,'package_record_changed'):voice.require_write_audit(self.prefix,'install',record_sha256='d'*64)
        self.path('before.json').write_text(self.path('before.json').read_text()+' ')
        with self.assertRaisesRegex(ValueError,'evidence_changed'):voice.require_write_audit(self.prefix,'install')
    def test_changed_helper_pins_and_missing_owned_lock_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'owned_lock_required'):
            with voice.native_write_audit(self.prefix,'install',self.command,self.inputs,None):self.fail('no lock')
        self.successful_fixture()
        with patch.object(voice,'audit_pins',return_value={'changed':'e'*64}):
            with self.assertRaisesRegex(ValueError,'not_successful'):voice.require_write_audit(self.prefix,'install')
    def test_catalog_and_catalog_package_keep_distinct_complete_audits(self):
        command=[sys.executable,'-c','pass']
        for phase in ('catalog','catalog-package'):
            with voice.native_write_audit(self.prefix,phase,command,self.inputs,self.lease) as audit:
                audit['command_exit']=subprocess.run(command,check=True,capture_output=True).returncode;audit['postcheck_exit']=0
            self.assertEqual(voice.require_write_audit(self.prefix,phase),voice.digest(voice.audit_path(self.prefix,phase,'complete.json')))
        self.assertNotEqual(voice.audit_path(self.prefix,'catalog','manifest.json'),voice.audit_path(self.prefix,'catalog-package','manifest.json'))
    def test_check_refuses_missing_audit_before_any_consumer_or_package_query(self):
        prepared=self.base/'voice-fixture.prepared.json';prepared.write_text('{}')
        qualified=self.base/'voice-fixture.qualified.json';qualified.write_text('{}')
        (self.base/'voice-fixture.installed.json').write_text(json.dumps({'record_sha256':'f'*64}))
        value={'version':voice.COMPONENTS['whisper-cpp'][1],'input':{'sha256':'a'*64}}
        with patch.object(voice,'prepared',return_value=(self.base,self.base,self.prefix,value)),patch.object(voice.subprocess,'run') as run,patch.object(voice,'isolated_job') as consumer:
            with self.assertRaises(FileNotFoundError):voice.check('whisper-cpp','fixture')
            run.assert_not_called();consumer.assert_not_called()


class DirectImportTests(unittest.TestCase):
    def test_direct_and_isolated_script_help_resolve_fixed_common_helpers(self):
        with tempfile.TemporaryDirectory() as cwd:
            (Path(cwd)/'run_step.py').write_text("raise RuntimeError('caller cwd must not supply helpers')")
            for flags in ([],['-I']):
                result=subprocess.run([sys.executable,*flags,'-B',str(ROOT/'scripts/build/phase2/voice_native.py'),'--help'],cwd=cwd,env={'PATH':os.environ['PATH']},capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,0,result.stderr);self.assertIn('catalog-package',result.stdout)

if __name__=='__main__':unittest.main()
