#!/usr/bin/env python3
"""Harmless native compile/stage plus actual namespace write/egress denials."""
import json
import fcntl
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

assert os.getuid() != 0
status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
assert int(status['CapEff'].strip(), 16) == 0
assert int(status['CapPrm'].strip(), 16) == 0
assert status['NoNewPrivs'].strip() == '1'
inherited_writable = []
for item in os.listdir('/proc/self/fd'):
    descriptor = int(item)
    if descriptor <= 2:
        continue
    try:
        flags = fcntl.fcntl(descriptor, fcntl.F_GETFL)
        target = os.readlink('/proc/self/fd/' + item)
    except OSError:
        continue
    if flags & os.O_ACCMODE in (os.O_WRONLY, os.O_RDWR):
        inherited_writable.append({'fd': descriptor, 'target': target})
assert not inherited_writable, inherited_writable
if '--hold-lock-check' in sys.argv:
    Path('/build/lock-probe-ready').write_text('ready')
    deadline = time.monotonic() + 5
    while not Path('/build/lock-probe-release').exists():
        assert time.monotonic() < deadline, 'parent lock check did not release probe'
        time.sleep(0.05)
denied = []
for path in ['/usr/toddy-denied', '/src/toddy-denied', '/etc/toddy-denied',
             '/root/toddy-denied', '/run/toddy-denied']:
    try:
        Path(path).write_text('must not be written')
    except OSError as exc:
        denied.append({'path': path, 'errno': exc.errno})
    else:
        raise AssertionError('outside write succeeded: ' + path)
assert not Path('/mnt/lfs').exists()
assert not Path('/sources').exists()
assert not Path('/run/dbus').exists()
assert not Path('/root').exists()
with socket.socket() as connection:
    connection.settimeout(1)
    try:
        connection.connect(('1.1.1.1', 443))
    except OSError as exc:
        network_error = exc.errno
    else:
        raise AssertionError('build namespace has external network')
Path('/build/hello.c').write_text('#include <stdio.h>\nint main(void){puts("toddy-native-isolated");return 0;}\n')
subprocess.run(['gcc', '/build/hello.c', '-o', '/stage/hello'], check=True)
result = subprocess.check_output(['/stage/hello'], text=True).strip()
assert result == 'toddy-native-isolated'
print(json.dumps({'uid': os.getuid(), 'gid': os.getgid(), 'cap_effective': 0,
                  'cap_permitted': 0, 'no_new_privileges': True,
                  'inherited_writable_fds': inherited_writable,
                  'outside_writes_denied': denied, 'external_network_errno': network_error,
                  'native_compile_stage_run': result, 'exit': 0}, indent=2))
