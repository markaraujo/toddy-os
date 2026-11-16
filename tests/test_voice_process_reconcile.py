"""Source contracts only; no native job, model, audio, VM or package execution."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('voice_reconcile_fixture',ROOT/'scripts/build/phase2/voice_process_reconcile.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


def proof():
    files={name:'a'*64 for name in ('process.py','child.py','artifacts.py','session.py')}
    transport={name:'b'*64 for name in ('capture','playback','device-list','pw-cat')}
    return {'tests_run':4,'errors':0,'failures':0,'skipped':0,'files':files,'file_sessions':{locale:{'transcript':'UNQUALIFIED SOURCE FIXTURE','word_error_rate':0.0} for locale in ('en','pt-BR')},'native_engine_stop':{'code':'canceled'},'transport':{name:{'sha256':sha} for name,sha in transport.items()}},files,transport


class RetryTests(unittest.TestCase):
    def test_frozen_driver_and_new_namespace_are_exact_without_edits_to_prepared_inputs(self):
        self.assertEqual(hashlib.sha256((ROOT/'scripts/build/phase2/voice_native.py').read_bytes()).hexdigest(),v.FROZEN_DRIVER)
        self.assertEqual(v.GENERATION,'native2');self.assertEqual(v.JOB,'voice-process-native2-r1')
        command=v.process_command(Path('/mnt/lfs/sources/phase2/inputs/voice-whisper-cpp-native2'))
        self.assertEqual(command[0],'/bin/bash');self.assertIn('/src/qualification/process-check.py',command)
        self.assertEqual(command[3],'/mnt/lfs/sources/phase2/work/voice-process-native2-r1')
        self.assertNotIn('/mnt/lfs/sources/phase2/work/voice-whisper-cpp-native2',command)

    def test_all_actual_process_runtime_transport_inference_and_stop_fields_required(self):
        value,files,transport=proof();v.validate_process(value,runtime_files=files,transport_files=transport)
        for field in ('tests','skip','runtime','transport','language','stop','transcript','wer'):
            changed=copy.deepcopy(value)
            if field=='tests':changed['tests_run']=True
            elif field=='skip':changed['skipped']=1
            elif field=='runtime':changed['files']['child.py']='c'*64
            elif field=='transport':del changed['transport']['pw-cat']
            elif field=='language':del changed['file_sessions']['pt-BR']
            elif field=='stop':changed['native_engine_stop']['code']='engine_failed'
            elif field=='transcript':changed['file_sessions']['en']['transcript']=''
            else:changed['file_sessions']['en']['word_error_rate']=float('nan')
            with self.subTest(field=field),self.assertRaises(ValueError):v.validate_process(changed,runtime_files=files,transport_files=transport)

    def test_help_imports_under_isolated_python_and_source_has_no_fake_old_exit_write(self):
        result=subprocess.run(['python3','-I',str(ROOT/'scripts/build/phase2/voice_process_reconcile.py'),'--help'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        source=(ROOT/'scripts/build/phase2/voice_process_reconcile.py').read_text()
        self.assertIn("b09-pipewire-tools-1.success.json",source)
        self.assertIn('frozen.require_write_audit',source);self.assertIn('frozen.native_write_audit',source)
        self.assertNotIn('frozen.read=',source);self.assertNotIn('frozen.prepared=',source)
        self.assertNotIn("write(Path(str(prefix)+'.process.exit.json')",source)
        self.assertNotIn('curl',source);self.assertNotIn('urlopen',source)


if __name__=='__main__':unittest.main()
