#!/usr/bin/env python3
"""Native file/HTTPS fixture for optional acquisition, no external network/model."""
import hashlib
import json
from pathlib import Path
import shlex
import re
import sys
import subprocess
import phase2_vm
ROOT=phase2_vm.ROOT
NAME=sys.argv[1] if len(sys.argv)>1 else 'acquisition-1'
assert re.fullmatch(r'acquisition-[1-9][0-9]*',NAME)
FILES=['runtime/acquisition/download.py','runtime/acquisition/choices.py','runtime/acquisition/cli.py',
       'tests/test_acquisition.py','config/phase2/local-model.lock.json']
if __name__=='__main__':
    payload={name:(ROOT/name).read_text() for name in FILES}
    remote='''from pathlib import Path
import fcntl,json,os,subprocess,sys
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
p=Path('/mnt/lfs/sources/phase2/inputs/acquisition-1');w=Path('/mnt/lfs/sources/phase2/work/acquisition-1')
assert not p.exists() and not w.exists(), 'Inspect existing job; no replay'
p.mkdir();w.mkdir();os.chown(w,101,101)
for name,text in json.load(sys.stdin).items():
    assert name in ['runtime/acquisition/download.py','runtime/acquisition/choices.py','runtime/acquisition/cli.py','tests/test_acquisition.py','config/phase2/local-model.lock.json']
    dest=p/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
'''
    remote=remote.replace('acquisition-1',NAME)
    state=ROOT/'.local/phase2'
    with (state/(NAME+'-dispatch.log')).open('xb') as log:
        subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(remote)],input=json.dumps(payload).encode(),stdout=log,stderr=subprocess.STDOUT,check=True)
        cmd='python3 /opt/toddy-build/scripts/build/phase2/job.py --loopback acquisition-1 /mnt/lfs/sources/phase2/inputs/acquisition-1 /mnt/lfs/sources/phase2/work/acquisition-1 python3 /src/tests/test_acquisition.py'
        result=subprocess.run(phase2_vm.ssh_args()+[cmd.replace('acquisition-1',NAME)],stdout=log,stderr=subprocess.STDOUT)
        (state/(NAME+'-dispatch.exit')).write_text(str(result.returncode)+'\n')
        if result.returncode:raise SystemExit(result.returncode)
    collect='''from pathlib import Path
import hashlib,json
p=Path('/var/log/toddy/phase2/acquisition-1')
assert p.with_suffix('.exit').read_text().strip()=='0'
log=p.with_suffix('.log').read_text();assert 'Ran 10 tests' in log and log.rstrip().endswith('OK')
root=Path('/mnt/lfs/sources/phase2/inputs/acquisition-1')
files=['runtime/acquisition/download.py','runtime/acquisition/choices.py','runtime/acquisition/cli.py','tests/test_acquisition.py','config/phase2/local-model.lock.json']
print(json.dumps({'job':'acquisition-1','scope':'native UID101 real TLS loopback + private file tests; no external acquisition or live API',
'exit':0,'tests':10,'log':log,'own_input_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in files}},indent=2))
'''
    result=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=collect.replace('acquisition-1',NAME).encode(),capture_output=True,check=True)
    report=json.loads(result.stdout)
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==sha for n,sha in report['own_input_sha256'].items())
    (ROOT/'docs/evidence/B03-acquisition.json').write_bytes(result.stdout)
    print(result.stdout.decode())
