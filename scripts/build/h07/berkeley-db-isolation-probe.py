#!/usr/bin/env python3
"""Measure the actual private test view before running the native suite."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

base = Path(sys.argv[1])
mode = sys.argv[2]
expected = json.loads((base / 'outer-namespaces.json').read_text())
current = {name: os.readlink('/proc/self/ns/' + name) for name in expected}
assert all(current[name] != expected[name] for name in expected)
assert os.path.samefile('/sources/db-5.3.28', base / 'source')
for visible, private in [('/tmp', 'tmp'), ('/var/tmp', 'var-tmp'), ('/dev/shm', 'shm')]:
    assert os.path.samefile(visible, base / 'runtime' / private)
assert hashlib.sha256(Path('/sources/db-5.3.28/test/tcl/repmgr007.tcl').read_bytes()).hexdigest() == 'f3ec292bdd03ea1066c683bde617ed27288c16c814a6eecd3a0cddd5a580fd44'
# statfs observes the effective mount, including when mountinfo has stacked entries.
shm_type = subprocess.check_output(
    ['/usr/bin/stat', '-f', '--format=%T', '/dev/shm'], text=True).strip()
assert shm_type == 'tmpfs', shm_type
Path('/tmp', 'toddy-bdb-' + base.name).write_text('private namespace only\n')
result = {'namespaces': current, 'pid': os.getpid(), 'private_pid_namespace': True,
          'canonical_source_is_private': True, 'tmp_var_tmp_shm_private': True,
          'shm_filesystem': shm_type, 'mode': mode}
(base / ('isolation-' + mode + '.json')).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result), flush=True)
