#!/usr/bin/env python3
"""Fresh private local-runtime owner; no model loading/preexec in broker threads."""
import json
import os
from pathlib import Path
import signal
import stat
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'broker'))
from protocol import encode, strict_json
from server import LocalRuntime, LocalRuntimeError


def main():
    if os.getuid() == 0:
        raise SystemExit(2)
    descriptor = int(os.environ.get('TODDY_LOCAL_BOOTSTRAP_FD', '-1'))
    try:
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or not 0 < info.st_size <= 65536):
            raise ValueError('invalid_bootstrap')
        data = os.pread(descriptor, 65537, 0)
        if len(data) != info.st_size:
            raise ValueError('invalid_bootstrap')
        bootstrap = strict_json(data)
    finally:
        os.close(descriptor)
    if not isinstance(bootstrap, dict) or set(bootstrap) != {'version', 'contract', 'model_path', 'runtime_directory'} or bootstrap['version'] != 1:
        raise ValueError('invalid_bootstrap')
    runtime = LocalRuntime(bootstrap['contract'], bootstrap['model_path'], bootstrap['runtime_directory'])
    def stop(*_):
        raise LocalRuntimeError('local_session_stopped')
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    # The installed user unit owns the complete helper/model cgroup. Replacing
    # the launcher's parent-death SIGKILL with SIGTERM allows ordinary cleanup.
    import ctypes
    if ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGTERM, 0, 0, 0) != 0:
        raise LocalRuntimeError('local_parent_watch_unavailable')
    try:
        connection = runtime.start(timeout=120)
        sys.stdout.buffer.write(encode({'version': 1, 'kind': 'local_ready',
            'connection': {'id': 'managed-local', 'socket_path': connection.socket_path,
                           'model_id': connection.model_id, 'credential': connection.credential}}))
        sys.stdout.buffer.flush()
        # Parent closes this private control pipe on task/worker completion.
        sys.stdin.buffer.read(1)
    except (Exception, KeyboardInterrupt):
        # No raw exception/startup log or ephemeral credential on diagnostics.
        return 2
    finally:
        runtime.stop()
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, LocalRuntimeError):
        raise SystemExit(2) from None
