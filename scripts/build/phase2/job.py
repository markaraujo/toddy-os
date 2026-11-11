#!/usr/bin/env python3
"""Guest compiler-job receipt; terminal exit is recorded independently of SSH."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--loopback', action='store_true',
                    help='Private inference namespace loopback; no external route')
parser.add_argument('--profile', choices=['standard','cups-local-resolver','samba-build-alias'],default='standard')
parser.add_argument('name')
parser.add_argument('input')
parser.add_argument('work')
parser.add_argument('command', nargs=argparse.REMAINDER)
args = parser.parse_args()
assert socket.gethostname() == 'toddy-builder' and os.getuid() == 0
assert re.fullmatch(r'[a-z][a-z0-9-]{1,63}', args.name) and args.command
assert Path(args.input).is_dir() and Path(args.work).is_dir(), 'Prepared input/work required before dispatch'
root = Path('/var/log/toddy/phase2')
root.mkdir(exist_ok=True)
prefix = root / args.name
with prefix.with_suffix('.dispatch.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not any(prefix.with_suffix(s).exists() for s in ['.job.json', '.log', '.exit']), 'Reconcile existing job; no replay'
    command = ['/bin/bash', '/opt/toddy-build/scripts/build/phase2/isolated.sh']
    if args.profile=='cups-local-resolver':
        assert args.input=='/mnt/lfs/sources/phase2/inputs/cups-2.4.19' and not args.loopback
        command[1]='/opt/toddy-build/scripts/build/phase2/cups-isolated.sh'
    if args.profile=='samba-build-alias':
        from samba_isolation import SOURCE, WORK
        assert (args.input, args.work) == (SOURCE, WORK)
        command[1]='/opt/toddy-build/scripts/build/phase2/samba-isolated.sh'
    if args.loopback:
        command.append('--loopback')
    command += [args.input, args.work, *args.command]
    record = {'pid': os.getpid(), 'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
              'proc_start_ticks': Path('/proc/self/stat').read_text().split()[21],
              'started_unix': time.time(), 'command': command,
              'harness_sha256': hashlib.sha256(Path(command[1]).read_bytes()).hexdigest()}
    if args.profile=='cups-local-resolver':
        record['profile_implementation_sha256']=hashlib.sha256(Path('/opt/toddy-build/scripts/build/phase2/cups_isolation.py').read_bytes()).hexdigest()
        record['base_harness_sha256']=hashlib.sha256(Path('/opt/toddy-build/scripts/build/phase2/isolated.sh').read_bytes()).hexdigest()
    if args.profile=='samba-build-alias':
        from samba_isolation import BASE_SHA, PROFILE_SHA
        record['profile_implementation_sha256']=hashlib.sha256(Path('/opt/toddy-build/scripts/build/phase2/samba_isolation.py').read_bytes()).hexdigest()
        record['base_harness_sha256']=BASE_SHA
        record['effective_harness_sha256']=PROFILE_SHA
    with prefix.with_suffix('.job.json').open('x') as output:
        json.dump(record, output, indent=2)
    with prefix.with_suffix('.log').open('xb') as log:
        result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        log.flush()
        os.fsync(log.fileno())
    part = prefix.with_suffix('.exit.part')
    part.write_text(str(result.returncode) + '\n')
    part.replace(prefix.with_suffix('.exit'))
    raise SystemExit(result.returncode)
