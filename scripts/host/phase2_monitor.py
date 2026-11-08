#!/usr/bin/env python3
"""Read-only deterministic long-job observation; never restarts or accepts a job."""
import argparse
import inspect
import re
import shlex
import subprocess

import phase2_vm

def cpu_progress(rows, owned, previous):
    current={(pid,rows[pid][2]):rows[pid][1] for pid in owned if pid in rows}
    delta=sum(max(0,ticks-previous.get(identity,0)) for identity,ticks in current.items())
    return delta,current


REMOTE = inspect.getsource(cpu_progress)+r'''
from pathlib import Path
import json,sys,time
name=sys.argv[1]; interval=int(sys.argv[2]); duration=int(sys.argv[3])
progress_path=Path(sys.argv[4]) if len(sys.argv)>4 and sys.argv[4] else None
if progress_path:
    assert progress_path.is_absolute() and progress_path.resolve().is_relative_to('/mnt/lfs/sources/phase2/work')
prefix=Path('/var/log/toddy/phase2')/name
job=json.loads(prefix.with_suffix('.job.json').read_text())
assert job['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
started=time.monotonic(); last_size=-1; progress=started
previous={};cpu=0;last_artifact=None
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
            rows[int(path.parent.name)]=(int(fields[1]),int(fields[11])+int(fields[12]),int(fields[19]))
        except (FileNotFoundError,ProcessLookupError,PermissionError):continue
    owned={job['pid']}
    while True:
        more={pid for pid,(parent,_,_) in rows.items() if parent in owned}-owned
        if not more:break
        owned.update(more)
    delta,previous=cpu_progress(rows,owned,previous);cpu+=delta
    size=prefix.with_suffix('.log').stat().st_size
    artifact=None
    if progress_path and progress_path.exists():
        assert progress_path.resolve().is_relative_to('/mnt/lfs/sources/phase2/work')
        st=progress_path.stat();artifact=(st.st_size,st.st_mtime_ns)
    if size!=last_size or delta>0 or artifact!=last_artifact:progress=time.monotonic()
    state={'job':name,'state':'running','elapsed_seconds':round(time.time()-job['started_unix']),
           'log_bytes':size,'processes':len(owned),'cpu_ticks':cpu,'cpu_delta_ticks':delta,
           'progress_log_bytes':artifact[0] if artifact else None,'idle_seconds':round(time.monotonic()-progress)}
    print(json.dumps(state),flush=True)
    if time.monotonic()-progress>=180:
        raise SystemExit(3)
    if time.monotonic()-started>=duration:
        print(json.dumps({'job':name,'state':'still-running','result':'not accepted; monitor window ended'}),flush=True)
        raise SystemExit(4)
    last_size=size;last_artifact=artifact
    time.sleep(interval)
'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job')
    parser.add_argument('--interval', type=int, default=60, choices=range(10, 61))
    parser.add_argument('--duration', type=int, default=1800, choices=range(60, 3601))
    parser.add_argument('--progress-log', help='Optional read-only compiler log under target phase2/work')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9-]{1,63}', args.job):
        raise SystemExit('Invalid job identity')
    result = subprocess.run(phase2_vm.ssh_args()+[shlex.join([
        'python3','-u','-',args.job,str(args.interval),str(args.duration),args.progress_log or ''])], input=REMOTE.encode())
    raise SystemExit(result.returncode)
