"""Bounded trusted-engine controls: parent death and no PGID signal after reap.

This is not unknown-code/escaped-descendant containment. Native qualification
binds fixed pw-cat/Whisper/eSpeak engines and their reviewed dependency closure.
"""
from dataclasses import dataclass
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

from .artifacts import VoiceError


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    elapsed_seconds: float
    released: bool


class ProcessRunner:
    def run(self, argv, *, cancel, timeout=30, release=None):
        if cancel.is_set():raise VoiceError('canceled')
        if not argv or not os.path.isabs(argv[0]) or isinstance(timeout,bool) or not 0<timeout<=300:
            raise VoiceError('process_arguments')
        if not hasattr(os,'WNOWAIT'):raise VoiceError('native_process_control_unavailable')
        environment={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'}
        runtime=os.environ.get('XDG_RUNTIME_DIR')
        if runtime and os.path.isabs(runtime):environment['XDG_RUNTIME_DIR']=runtime
        started=time.monotonic()
        try:
            proc=subprocess.Popen([sys.executable,'-I','-B',str(Path(__file__).with_name('child.py')),str(os.getpid()),*argv],
                stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                close_fds=True,start_new_session=True,env=environment,umask=0o077)
        except OSError as exc:raise VoiceError('engine_unavailable') from exc
        owned=True
        def status():
            nonlocal owned
            try:return os.waitid(os.P_PID,proc.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
            except ChildProcessError:
                # Another reaper is unexpected; never signal a now-reusable PGID.
                owned=False
                raise VoiceError('voice_process_ownership_lost') from None
        def send(sig):
            if owned:
                try:os.killpg(proc.pid,sig)
                except ProcessLookupError:pass
        selector=selectors.DefaultSelector()
        for stream in (proc.stdout,proc.stderr):
            os.set_blocking(stream.fileno(),False);selector.register(stream,selectors.EVENT_READ)
        total=0;released=False;release_time=None
        try:
            while True:
                exited=status()  # WNOWAIT reserves the leader PID through cleanup.
                if not selector.get_map() and exited is not None:break
                now=time.monotonic()
                if cancel.is_set():raise VoiceError('canceled')
                if now-started>timeout:raise VoiceError('voice_deadline')
                if release is not None and release.is_set() and not released and exited is None:
                    send(signal.SIGINT);released=True;release_time=now
                if release_time is not None and now-release_time>2 and exited is None:
                    raise VoiceError('capture_stop_failed')
                for key,_ in selector.select(.025):
                    chunk=os.read(key.fileobj.fileno(),8192)
                    if not chunk:selector.unregister(key.fileobj);continue
                    total+=len(chunk)
                    if total>65536:raise VoiceError('engine_output_limit')
            code=exited.si_status if exited.si_code==os.CLD_EXITED else -exited.si_status
            allowed=(0,-signal.SIGINT,128+signal.SIGINT) if released else (0,)
            if code not in allowed:raise VoiceError('engine_failed')
            return ProcessResult(code,time.monotonic()-started,released)
        finally:
            # All group signals precede the one reap, even if the leader already
            # exited and a trusted descendant still holds a diagnostic pipe.
            try:
                if owned:
                    try:
                        send(signal.SIGTERM)
                        until=time.monotonic()+.5
                        while status() is None and time.monotonic()<until:time.sleep(.01)
                        send(signal.SIGKILL)
                    finally:
                        if owned:
                            proc.wait(timeout=1)
                            owned=False
            finally:
                selector.close();proc.stdout.close();proc.stderr.close()
