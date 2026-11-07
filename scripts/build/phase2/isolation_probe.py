#!/usr/bin/env python3
"""Harmless native compile/stage plus actual namespace write/egress denials."""
import json
import os
from pathlib import Path
import socket
import subprocess

assert os.getuid() != 0
status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
assert int(status['CapEff'].strip(), 16) == 0
assert int(status['CapPrm'].strip(), 16) == 0
assert status['NoNewPrivs'].strip() == '1'
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
                  'outside_writes_denied': denied, 'external_network_errno': network_error,
                  'native_compile_stage_run': result, 'exit': 0}, indent=2))
