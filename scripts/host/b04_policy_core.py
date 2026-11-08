#!/usr/bin/env python3
"""Native independent executor policy/operation core; no root IPC claim."""
import hashlib
import json
from pathlib import Path
import shlex
import re
import sys
import subprocess
import phase2_vm
ROOT=phase2_vm.ROOT
NAME=sys.argv[1] if len(sys.argv)>1 else 'policy-core-1'
assert re.fullmatch(r'policy-core-[1-9][0-9]*',NAME)
FILES=['runtime/executor/store.py','tests/test_executor_store.py']
if __name__=='__main__':
    payload={name:(ROOT/name).read_text() for name in FILES}
    remote='''from pathlib import Path
import fcntl,json,os,subprocess,sys
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
p=Path('/mnt/lfs/sources/phase2/inputs/policy-core-1');w=Path('/mnt/lfs/sources/phase2/work/policy-core-1')
assert not p.exists() and not w.exists(), 'Inspect existing job; no replay'
p.mkdir();w.mkdir();os.chown(w,101,101)
for name,text in json.load(sys.stdin).items():
    assert name in ['runtime/executor/store.py','tests/test_executor_store.py']
    dest=p/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
'''
    remote=remote.replace('policy-core-1',NAME)
    state=ROOT/'.local/phase2'
    with (state/(NAME+'-dispatch.log')).open('xb') as log:
        subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(remote)],input=json.dumps(payload).encode(),stdout=log,stderr=subprocess.STDOUT,check=True)
        cmd='python3 /opt/toddy-build/scripts/build/phase2/job.py policy-core-1 /mnt/lfs/sources/phase2/inputs/policy-core-1 /mnt/lfs/sources/phase2/work/policy-core-1 python3 /src/tests/test_executor_store.py'
        result=subprocess.run(phase2_vm.ssh_args()+[cmd.replace('policy-core-1',NAME)],stdout=log,stderr=subprocess.STDOUT)
        (state/(NAME+'-dispatch.exit')).write_text(str(result.returncode)+'\n')
        if result.returncode:raise SystemExit(result.returncode)
    collect='''from pathlib import Path
import hashlib,json
p=Path('/var/log/toddy/phase2/policy-core-1')
assert p.with_suffix('.exit').read_text().strip()=='0'
log=p.with_suffix('.log').read_text();assert 'Ran 8 tests' in log and log.rstrip().endswith('OK')
root=Path('/mnt/lfs/sources/phase2/inputs/policy-core-1')
files=['runtime/executor/store.py','tests/test_executor_store.py']
print(json.dumps({'job':'policy-core-1','scope':'native UID101 policy/SQLite/process-loss tests only; no authenticated root IPC',
'exit':0,'tests':8,'log':log,'own_input_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in files}},indent=2))
'''
    result=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=collect.replace('policy-core-1',NAME).encode(),capture_output=True,check=True)
    report=json.loads(result.stdout)
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==sha for n,sha in report['own_input_sha256'].items())
    (ROOT/'docs/evidence/B04-policy-core.json').write_bytes(result.stdout)
    print(result.stdout.decode())
