"""Real process loss/Stop/reap checks only; no speech engine/audio activation."""
import ctypes
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from runtime.voice.process import ProcessRunner
from runtime.voice.artifacts import VoiceError
ROOT=Path(__file__).resolve().parents[1]


class VoiceProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        libc=ctypes.CDLL(None,use_errno=True);prior=ctypes.c_int()
        self.subreaper=libc.prctl(37,ctypes.byref(prior),0,0,0)==0 and libc.prctl(36,1,0,0,0)==0
        if self.subreaper:self.addCleanup(lambda:libc.prctl(36,prior.value,0,0,0))
    def wait(self,path):
        deadline=time.monotonic()+3
        while not path.exists():
            if time.monotonic()>deadline:raise AssertionError('process fixture not ready')
            time.sleep(.01)

    def test_group_signals_are_before_reap_even_when_leader_exited_and_child_holds_pipe(self):
        if not self.subreaper:self.skipTest('test process subreaper unavailable')
        engine=self.base/'fork-fixture';marker=self.base/'descendant'
        engine.write_text('#!/usr/bin/python3\nimport os,time,pathlib\npid=os.fork()\nif pid==0:time.sleep(30)\nelse:pathlib.Path('+repr(str(marker))+').write_text(str(pid))\n')
        engine.chmod(0o700);observed=[];real=os.killpg
        def checked(pgid,sig):
            # A zombie leader is still a reserved PID/PGID, not a reusable one.
            self.assertTrue(Path('/proc',str(pgid),'stat').exists())
            observed.append((pgid,sig));return real(pgid,sig)
        with patch('runtime.voice.process.os.killpg',checked):
            with self.assertRaisesRegex(VoiceError,'deadline'):
                ProcessRunner().run([str(engine)],cancel=threading.Event(),timeout=.2)
        self.assertEqual([sig for _,sig in observed],[signal.SIGTERM,signal.SIGKILL])
        self.assertFalse(Path('/proc',str(observed[0][0])).exists())
        child=int(marker.read_text());self.assertEqual(os.waitpid(child,0)[0],child)

    def test_actual_parent_loss_kills_direct_trusted_engine_before_audio_can_continue(self):
        # Per-test-process subreaping lets us reap the orphan and prove actual
        # exit without depending on a container's PID1 zombie behavior.
        libc=ctypes.CDLL(None,use_errno=True);prior=ctypes.c_int()
        if libc.prctl(37,ctypes.byref(prior),0,0,0)!=0 or libc.prctl(36,1,0,0,0)!=0:
            self.skipTest('test process subreaper unavailable')
        marker=self.base/'ready';engine=self.base/'long-fixture'
        engine.write_text('#!/usr/bin/python3\nimport os,pathlib,signal,time\nsignal.signal(signal.SIGTERM,signal.SIG_IGN)\npathlib.Path('+repr(str(marker))+').write_text(str(os.getpid()))\ntime.sleep(30)\n')
        engine.chmod(0o700)
        code='import sys,threading;sys.path.insert(0,'+repr(str(ROOT))+');from runtime.voice.process import ProcessRunner;ProcessRunner().run(['+repr(str(engine))+'],cancel=threading.Event(),timeout=30)'
        parent=subprocess.Popen([sys.executable,'-I','-c',code],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        pid=None
        try:
            self.wait(marker);pid=int(marker.read_text());parent.kill();parent.wait(timeout=3)
            deadline=time.monotonic()+3;result=(0,0)
            while time.monotonic()<deadline:
                try:result=os.waitpid(pid,os.WNOHANG)
                except ChildProcessError:time.sleep(.01);continue
                if result[0]==pid:break
                time.sleep(.01)
            self.assertEqual(result[0],pid)
            self.assertTrue(os.WIFSIGNALED(result[1]));self.assertEqual(os.WTERMSIG(result[1]),signal.SIGKILL)
        finally:
            if parent.poll() is None:parent.kill();parent.wait(timeout=3)
            if pid is not None and Path('/proc',str(pid)).exists():
                try:os.kill(pid,signal.SIGKILL);os.waitpid(pid,0)
                except (ProcessLookupError,ChildProcessError):pass
            libc.prctl(36,prior.value,0,0,0)

    def test_bounded_device_metadata_stdout_never_returns_diagnostics(self):
        result=ProcessRunner().run([sys.executable,'-c',
            'import sys;print("[]");print("private diagnostic fixture",file=sys.stderr)'],
            cancel=threading.Event(),timeout=2,capture_stdout=True,output_limit=1024)
        self.assertEqual(result.stdout,b'[]\n')
        self.assertNotIn(b'private',result.stdout)

    def test_launcher_refuses_wrong_parent_before_exec(self):
        marker=self.base/'should-not-exist'
        result=subprocess.run([sys.executable,'-I',str(ROOT/'runtime/voice/child.py'),'0',
            sys.executable,'-c','from pathlib import Path;Path('+repr(str(marker))+').touch()'],
            capture_output=True,timeout=3)
        self.assertEqual(result.returncode,125);self.assertFalse(marker.exists())


if __name__=='__main__':unittest.main()
