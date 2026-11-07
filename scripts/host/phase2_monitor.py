#!/usr/bin/env python3
"""Read-only deterministic long-job observation; never restarts or accepts a job."""
import argparse
import re
import subprocess

import phase2_vm

REMOTE = r'''
from pathlib import Path
import json,sys,time
name=sys.argv[1]; interval=int(sys.argv[2]); duration=int(sys.argv[3])
prefix=Path('/var/log/toddy/phase2')/name
job=json.loads(prefix.with_suffix('.job.json').read_text())
assert job['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
started=time.monotonic(); last_size=-1; last_cpu=-1; progress=started
while True:
    terminal=prefix.with_suffix('.exit')
    if terminal.exists():
        result=int(terminal.read_text().strip())
        print(json.dumps({'job':name,'state':'terminal','exit':result,'postconditions':'must be checked separately'}),flush=True)
        raise SystemExit(0 if result==0 else 1)
    proc=Path('/proc')/str(job['pid'])
    if not proc.exists() or proc.joinpath('stat').read_text().split()[21]!=job['proc_start_ticks']:
        print(json.dumps({'job':name,'state':'uncertain','reason':'PID identity absent/changed without exit receipt'}),flush=True)
        raise SystemExit(2)
    rows={}
    for path in Path('/proc').glob('[0-9]*/stat'):
        try:
            fields=path.read_text().rpartition(') ')[2].split()
            rows[int(path.parent.name)]=(int(fields[1]),int(fields[11])+int(fields[12]))
        except (FileNotFoundError,ProcessLookupError,PermissionError):continue
    owned={job['pid']}
    while True:
        more={pid for pid,(parent,_) in rows.items() if parent in owned}-owned
        if not more:break
        owned.update(more)
    cpu=sum(rows.get(pid,(0,0))[1] for pid in owned)
    size=prefix.with_suffix('.log').stat().st_size
    if size!=last_size or cpu>last_cpu:progress=time.monotonic()
    state={'job':name,'state':'running','elapsed_seconds':round(time.time()-job['started_unix']),
           'log_bytes':size,'processes':len(owned),'cpu_ticks':cpu,'idle_seconds':round(time.monotonic()-progress)}
    print(json.dumps(state),flush=True)
    if time.monotonic()-progress>=180:
        raise SystemExit(3)
    if time.monotonic()-started>=duration:
        print(json.dumps({'job':name,'state':'still-running','result':'not accepted; monitor window ended'}),flush=True)
        raise SystemExit(4)
    last_size=size;last_cpu=cpu
    time.sleep(interval)
'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job')
    parser.add_argument('--interval', type=int, default=60, choices=range(10, 61))
    parser.add_argument('--duration', type=int, default=1800, choices=range(60, 3601))
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9-]{1,63}', args.job):
        raise SystemExit('Invalid job identity')
    result = subprocess.run(phase2_vm.ssh_args()+[
        f'python3 -u - {args.job} {args.interval} {args.duration}'], input=REMOTE.encode())
    raise SystemExit(result.returncode)
