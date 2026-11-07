#!/usr/bin/env python3
"""Success-gated Node compile -> native package handoff, with no uncertain replay."""
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import phase2_vm

ROOT = phase2_vm.ROOT
STATE = ROOT / '.local/phase2'


def inputs():
    paths = [p for p in (ROOT/'scripts/build').rglob('*')
             if p.is_file() and p.suffix in ('.py', '.sh', '.c', '.cpp', '.tcl')]
    paths += [ROOT/'config'/name for name in ['sources.lock.json','books.lock.json',
        'supplemental-sources.lock.json','security-overlay.lock.json',
        'component-licenses.json','package-ownership-policy.json','phase2/sources.lock.json']]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def record(data):
    path = STATE/'node-handoff.json'
    part = path.with_suffix('.json.part')
    part.write_text(json.dumps(data, indent=2)+'\n')
    part.replace(path)
    print(json.dumps({k:v for k,v in data.items() if k != 'inputs'}), flush=True)


if __name__ == '__main__':
    STATE.mkdir(exist_ok=True)
    with (STATE/'node-handoff.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        pinned = inputs()
        data = {'scope':'B01 native Node handoff only; no story/G2 acceptance',
                'inputs':pinned, 'state':'waiting for actual compile exit', 'pid':__import__('os').getpid()}
        record(data)
        # This monitor is read-only, never restarts the build, and returns nonzero
        # for missing identity/exit, stalled observation, failure or window end.
        result = subprocess.run([sys.executable, str(ROOT/'scripts/host/phase2_monitor.py'),
                                 'node-bootstrap-1', '--duration', '3600'])
        if result.returncode:
            data.update(state='no guest handoff performed', monitor_exit=result.returncode)
            record(data)
            raise SystemExit(result.returncode)
        if pinned != inputs():
            data.update(state='source changed; no guest handoff performed')
            record(data)
            raise SystemExit(65)
        # Never replay any prior uncertain/terminal native transaction.
        inspect = """from pathlib import Path
import json
p=Path('/var/log/toddy/build/b01-node-bootstrap-install')
found=[str(p)+s for s in ['.running.json','.failed.json','.success.json'] if Path(str(p)+s).exists()]
assert not found, 'Existing transaction; reconcile instead of replay: '+str(found)
assert Path('/var/log/toddy/phase2/node-bootstrap-1.exit').read_text().strip()=='0'
"""
        subprocess.run(phase2_vm.ssh_args()+['python3 -'], input=inspect.encode(), check=True)
        data.update(state='compile exit zero; syncing exact reviewed metadata')
        record(data)
        subprocess.run([sys.executable, str(ROOT/'scripts/host/phase2_sync.py'), '--metadata-only'], check=True)
        data.update(state='native package transaction active', guest_prefix='/var/log/toddy/build/b01-node-bootstrap-install')
        record(data)
        command = 'cd /opt/toddy-build/scripts/build && python3 run_step.py b01-node-bootstrap-install phase2/node-install.sh phase2/node-check.sh --user root'
        with (STATE/'node-install.log').open('ab') as log:
            result = subprocess.run(phase2_vm.ssh_args()+[command], stdout=log, stderr=subprocess.STDOUT)
        # A lost transport remains uncertain even if a marker later appears.
        data.update(state='native transaction command returned', command_exit=result.returncode,
                    next_action='Read actual guest success/failed/running marker, package payload and postconditions before any new write.')
        record(data)
        raise SystemExit(result.returncode)
