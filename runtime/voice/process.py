"""Bounded cancellable trusted-engine subprocesses; no shell and no audio on import."""
from dataclasses import dataclass
import os
import selectors
import signal
import subprocess
import time

from runtime.voice.artifacts import VoiceError


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    elapsed_seconds: float
    released: bool


class ProcessRunner:
    def run(self, argv, *, cancel, timeout=30, release=None):
        if cancel.is_set():
            raise VoiceError('canceled')
        if not argv or not os.path.isabs(argv[0]) or not 0 < timeout <= 300:
            raise VoiceError('process_arguments')
        environment={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'}
        runtime=os.environ.get('XDG_RUNTIME_DIR')
        if runtime and os.path.isabs(runtime):
            environment['XDG_RUNTIME_DIR']=runtime
        started=time.monotonic()
        try:
            proc=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                close_fds=True,start_new_session=True,env=environment,umask=0o077)
        except OSError as exc:
            raise VoiceError('engine_unavailable') from exc
        selector=selectors.DefaultSelector()
        for stream in (proc.stdout,proc.stderr):
            os.set_blocking(stream.fileno(),False)
            selector.register(stream,selectors.EVENT_READ)
        total=0
        released=False
        release_time=None
        completed=False
        try:
            while selector.get_map() or proc.poll() is None:
                now=time.monotonic()
                if cancel.is_set():
                    raise VoiceError('canceled')
                if now-started>timeout:
                    raise VoiceError('voice_deadline')
                if release is not None and release.is_set() and not released and proc.poll() is None:
                    os.killpg(proc.pid,signal.SIGINT)
                    released=True
                    release_time=now
                if release_time is not None and now-release_time>2 and proc.poll() is None:
                    raise VoiceError('capture_stop_failed')
                for key,_ in selector.select(0.025):
                    chunk=os.read(key.fileobj.fileno(),8192)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    total+=len(chunk)
                    if total>65536:
                        raise VoiceError('engine_output_limit')
            status=proc.wait()
            allowed=(0,-signal.SIGINT,128+signal.SIGINT) if released else (0,)
            if status not in allowed:
                raise VoiceError('engine_failed')
            completed=True
            return ProcessResult(status,time.monotonic()-started,released)
        finally:
            # Engines are trusted installed components, not an unknown-code
            # sandbox. Native service/cgroup qualification remains required.
            if not completed or proc.poll() is None:
                try:
                    os.killpg(proc.pid,signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    proc.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(proc.pid,signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait(timeout=1)
                if not completed:
                    try:
                        os.killpg(proc.pid,signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            selector.close()
            proc.stdout.close()
            proc.stderr.close()
