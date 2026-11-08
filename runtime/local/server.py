"""Owned unprivileged local-model process, private Unix transport and lifecycle."""
from dataclasses import dataclass, field
from contextlib import closing
import hashlib
import http.client
import os
from pathlib import Path
import resource
import secrets
import shutil
import signal
import socket
import stat
import subprocess
import tempfile
import time


class LocalRuntimeError(RuntimeError):
    """Stable non-secret setup/runtime error; never include raw process output."""


@dataclass(frozen=True)
class LocalConnection:
    socket_path: str
    model_id: str
    credential: str = field(repr=False)


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, path, timeout=5):
        super().__init__('toddy.local', timeout=timeout)
        self.path = str(path)

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.path)


class LocalRuntime:
    """One qualified text model; caller owns task policy and session shutdown.

    Connection objects are private broker/worker inputs, never profile exports,
    diagnostics or capability JSON. This process has no administrative authority.
    """
    def __init__(self, contract, model_path, runtime_directory):
        if os.getuid() == 0:
            raise LocalRuntimeError('local_runtime_requires_user')
        self.contract = contract
        self.model_path = Path(model_path)
        self.runtime_root = Path(runtime_directory)
        self.process = None
        self.directory = None
        self._connection = None
        self._model_fd = None
        self.load_seconds = None
        self.last_stop = None
        self.last_error = None

    def start(self, timeout=120):
        if self.process is not None or self.directory is not None:
            raise LocalRuntimeError('local_runtime_already_started')
        flags = set(next(l for l in Path('/proc/cpuinfo').read_text().splitlines()
                         if l.startswith('flags')).split(':', 1)[1].split())
        if not set(self.contract['runtime']['required_cpu_flags']) <= flags:
            raise LocalRuntimeError('local_cpu_profile_unavailable')
        if self.model_path.is_symlink() or self.model_path.resolve() != self.model_path:
            raise LocalRuntimeError('model_path_redirected')
        self.runtime_root.mkdir(mode=0o700, exist_ok=True)
        info = self.runtime_root.lstat()
        if (self.runtime_root.resolve() != self.runtime_root or not stat.S_ISDIR(info.st_mode)
                or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700):
            raise LocalRuntimeError('private_runtime_directory_required')
        memory = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
        needed_kib = (self.contract['budgets']['proposed_model_peak_rss_mib']+512)*1024
        if int(memory['MemAvailable'].split()[0]) < needed_kib:
            raise LocalRuntimeError('local_memory_insufficient')
        started = time.monotonic()
        try:
            self._model_fd = os.open(self.model_path, os.O_RDONLY | os.O_NOFOLLOW)
            info = os.fstat(self._model_fd)
            model = self.contract['model']
            if not stat.S_ISREG(info.st_mode) or info.st_size != model['bytes']:
                raise LocalRuntimeError('model_size_mismatch')
            with os.fdopen(os.dup(self._model_fd), 'rb') as incoming:
                if hashlib.file_digest(incoming, 'sha256').hexdigest() != model['sha256']:
                    raise LocalRuntimeError('model_integrity_mismatch')
            os.lseek(self._model_fd, 0, os.SEEK_SET)
            self.directory = Path(tempfile.mkdtemp(prefix='local-', dir=self.runtime_root))
            endpoint = self.directory/'server.sock'
            if len(os.fsencode(endpoint)) > 100:
                raise LocalRuntimeError('local_socket_path_too_long')
            credential = secrets.token_hex(32)
            keypath = self.directory/'key'
            descriptor = os.open(keypath, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(descriptor, 'w') as output:
                output.write(credential+'\n')
            model_id = 'toddy-qwen3-1.7b-q8_0'
            self._connection = LocalConnection(str(endpoint), model_id, credential)
            threads = self.contract['runtime']['threads']
            cpus = sorted(os.sched_getaffinity(0))[:threads]

            def limits():
                os.sched_setaffinity(0, cpus)
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
                resource.setrlimit(resource.RLIMIT_AS, (8192*1024**2, 8192*1024**2))

            command = ['/usr/bin/llama-server', '-m', f'/proc/self/fd/{self._model_fd}',
                       '--alias', model_id, '--host', str(endpoint), '--api-key-file', str(keypath),
                       '--threads', str(threads), '--threads-batch', str(threads), '--threads-http', '2',
                       '--parallel', '1', '--ctx-size', str(self.contract['runtime']['context_tokens']),
                       '--batch-size', '512', '--ubatch-size', '128', '--n-gpu-layers', '0',
                       '--offline', '--no-slots', '--no-webui', '--poll', '0',
                       '--chat-template-kwargs', '{"enable_thinking":false}', '--log-disable']
            fd = os.open(self.directory/'server.log', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as log:
                self.process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log,
                    stderr=subprocess.STDOUT, pass_fds=(self._model_fd,), preexec_fn=limits,
                    env={'PATH':'/usr/bin:/usr/sbin','HOME':str(self.directory),
                         'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','OMP_NUM_THREADS':str(threads)})
            deadline = time.monotonic()+timeout
            while True:
                if self.process.poll() is not None:
                    raise LocalRuntimeError('local_process_exited')
                if time.monotonic() >= deadline:
                    raise LocalRuntimeError('local_readiness_deadline')
                try:
                    with closing(UnixHTTPConnection(endpoint, timeout=1)) as connection:
                        connection.request('GET', '/health', headers={'Authorization':'Bearer '+credential})
                        response = connection.getresponse()
                        response.read(4096)
                        if response.status == 200:
                            break
                except OSError:
                    pass
                time.sleep(.1)
            self.load_seconds = time.monotonic()-started
            return self._connection
        except Exception as error:
            # Keep bounded startup diagnostics privately before deleting the
            # ephemeral key/socket. No prompt has been dispatched at this stage.
            self.last_error = str(error) if isinstance(error, LocalRuntimeError) else 'local_start_failed'
            if self.directory is not None and (self.directory/'server.log').exists():
                text = (self.directory/'server.log').read_bytes()[-4096:]
                if self._connection is not None:
                    text = text.replace(self._connection.credential.encode(), b'[credential]')
                descriptor, temporary = tempfile.mkstemp(prefix='.error-', dir=self.runtime_root)
                with os.fdopen(descriptor, 'wb') as output:
                    output.write(text)
                os.replace(temporary, self.runtime_root/'last-startup-error.log')
            self.stop()
            raise

    def stop(self):
        """Idempotent process reconciliation, without any model/tool write replay."""
        forced = False
        code = None
        if self.process is not None:
            if self.process.poll() is None:
                self.process.send_signal(signal.SIGTERM)
            try:
                code = self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                forced = True
                self.process.kill()
                code = self.process.wait()
            self.process = None
        if self._model_fd is not None:
            os.close(self._model_fd)
            self._model_fd = None
        if self.directory is not None:
            shutil.rmtree(self.directory)
            self.directory = None
        self._connection = None
        if code is not None:
            self.last_stop = {'exit':code,'forced':forced,'private_state_removed':True}
        return self.last_stop

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()
