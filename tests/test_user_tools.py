"""Actual unprivileged files/processes, without claiming plugin confinement."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/tools'))
from native import Tools,ToolError

class UserToolTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'workspace';self.path.mkdir(mode=0o700)
        self.tools=Tools(self.path)
    def tearDown(self):self.tools.close();self.temp.cleanup()
    def test_read_write_exact_hash_and_configuration_preservation(self):
        first=self.tools.write('file.txt','Olá 世界',None)
        self.assertTrue(first['verified']);self.assertEqual(self.tools.read('file.txt')['text'],'Olá 世界')
        (self.path/'file.txt').chmod(0o640)
        second=self.tools.write('file.txt','changed',first['sha256']);self.assertNotEqual(second['sha256'],first['sha256'])
        self.assertEqual((self.path/'file.txt').stat().st_mode&0o777,0o640)
        with self.assertRaisesRegex(ToolError,'file_changed'):self.tools.write('file.txt','bad overwrite',first['sha256'])
        self.assertEqual(self.tools.read('file.txt')['text'],'changed')
    def test_path_symlink_hardlink_fifo_and_size_denial(self):
        for path in ('../outside','/etc/passwd','sub/../file','sub//file',''):
            with self.assertRaisesRegex(ToolError,'invalid_relative_path'):self.tools.read(path)
        outside=Path(self.temp.name)/'outside';outside.write_text('preserve')
        (self.path/'link').symlink_to(outside)
        with self.assertRaises(OSError):self.tools.read('link')
        with self.assertRaises(OSError):self.tools.write('link','overwrite',None)
        os.link(outside,self.path/'hardlink')
        with self.assertRaisesRegex(ToolError,'file_type_or_size_limit'):self.tools.read('hardlink')
        os.mkfifo(self.path/'fifo')
        started=time.monotonic()
        with self.assertRaisesRegex(ToolError,'file_type_or_size_limit'):self.tools.read('fifo')
        self.assertLess(time.monotonic()-started,1)
        (self.path/'huge').write_bytes(b'x'*65537)
        with self.assertRaisesRegex(ToolError,'file_type_or_size_limit'):self.tools.read('huge')
        self.assertEqual(outside.read_text(),'preserve')
    def test_shell_actual_user_cwd_clean_environment(self):
        os.environ['TODDY_DUMMY_SECRET']='do-not-inherit'
        try:
            result=self.tools.shell([sys.executable,'-c','import os,json; print(json.dumps([os.getuid(),os.getcwd(),os.getenv("TODDY_DUMMY_SECRET")]))'])
        finally:os.environ.pop('TODDY_DUMMY_SECRET')
        import json
        uid,cwd,secret=json.loads(result['output'])
        self.assertEqual(uid,os.getuid());self.assertNotEqual(uid,0);self.assertEqual(cwd,str(self.path));self.assertIsNone(secret)
        self.assertEqual(result['exit'],0);self.assertFalse(result['side_effects_verified'])
    def test_active_stop_no_silent_rollback_or_leftover_process(self):
        stop=threading.Event();results=[]
        code="from pathlib import Path;import os,time;Path('started').write_text(str(os.getpid()));time.sleep(20)"
        def run():
            try:self.tools.shell([sys.executable,'-c',code],canceled=stop.is_set)
            except ToolError as error:results.append(str(error))
        thread=threading.Thread(target=run);thread.start()
        try:
            deadline=time.monotonic()+5
            while not (self.path/'started').exists() and time.monotonic()<deadline:time.sleep(.01)
            self.assertTrue((self.path/'started').exists());pid=int((self.path/'started').read_text())
            began=time.monotonic();stop.set();thread.join(2)
            self.assertFalse(thread.is_alive());self.assertLess(time.monotonic()-began,2)
            self.assertEqual(results,['canceled_effects_unverified'])
            with self.assertRaises(ProcessLookupError):os.kill(pid,0)
            self.assertTrue((self.path/'started').exists())
        finally:stop.set();thread.join(3)
    def test_shell_output_deadline_and_explicit_argv(self):
        with self.assertRaisesRegex(ToolError,'invalid_shell_arguments'):self.tools.shell(['relative-command'])
        for code,error in [('print("x"*70000)','shell_output_limit'),('import time;time.sleep(10)','shell_deadline')]:
            with self.assertRaisesRegex(ToolError,error):self.tools.shell([sys.executable,'-c',code],timeout_seconds=1)

if __name__=='__main__':unittest.main(verbosity=2)
