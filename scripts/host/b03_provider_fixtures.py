#!/usr/bin/env python3
"""Dispatch offline native Pi protocol fixtures; no model or package rebuild."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import phase2_vm

ROOT = phase2_vm.ROOT
FILES = ['provider.mjs', 'local-transport.mjs', 'provider-fixtures.mjs']

if __name__ == '__main__':
    payload = {name: (ROOT/'runtime/engine'/name).read_text() for name in FILES}
    remote = '''from pathlib import Path
import fcntl,json,os,shutil,subprocess,sys
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
p=Path('/mnt/lfs/sources/phase2/inputs/provider-fixtures-1')
w=Path('/mnt/lfs/sources/phase2/work/provider-fixtures-1')
assert not p.exists() and not w.exists(), 'Reconcile existing fixture input/job; no replay'
p.mkdir();w.mkdir();os.chown(w,101,101)
shutil.copytree('/mnt/lfs/sources/phase2/inputs/local-model-proof/node_modules',p/'node_modules',symlinks=True)
for name,text in json.load(sys.stdin).items():
    assert name in ['provider.mjs','local-transport.mjs','provider-fixtures.mjs']
    (p/name).write_text(text)
'''
    import shlex
    state=ROOT/'.local/phase2'
    with (state/'provider-fixtures-1-dispatch.log').open('xb') as log:
        subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(remote)],
                       input=json.dumps(payload).encode(),stdout=log,stderr=subprocess.STDOUT,check=True)
        command='python3 /opt/toddy-build/scripts/build/phase2/job.py provider-fixtures-1 /mnt/lfs/sources/phase2/inputs/provider-fixtures-1 /mnt/lfs/sources/phase2/work/provider-fixtures-1 node /src/provider-fixtures.mjs'
        result=subprocess.run(phase2_vm.ssh_args()+[command],stdout=log,stderr=subprocess.STDOUT)
        (state/'provider-fixtures-1-dispatch.exit').write_text(str(result.returncode)+'\n')
        if result.returncode: raise SystemExit(result.returncode)
    collect='''from pathlib import Path
import hashlib,json
p=Path('/var/log/toddy/phase2/provider-fixtures-1')
assert p.with_suffix('.exit').read_text().strip()=='0'
lines=p.with_suffix('.log').read_text().splitlines()
d=json.loads(lines[-1]);d['native_job']='provider-fixtures-1'
d['expected_malformed_sdk_stderr_lines']=len(lines)-1
root=Path('/mnt/lfs/sources/phase2/inputs/provider-fixtures-1')
d['own_input_sha256']={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['provider.mjs','local-transport.mjs','provider-fixtures.mjs']}
d['node_version']=__import__('subprocess').check_output(['chroot','/mnt/lfs','node','--version'],text=True).strip()
print(json.dumps(d,indent=2))
'''
    collected=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=collect.encode(),capture_output=True,check=True)
    report=json.loads(collected.stdout)
    assert all(hashlib.sha256((ROOT/'runtime/engine'/n).read_bytes()).hexdigest()==sha for n,sha in report['own_input_sha256'].items())
    (ROOT/'docs/evidence/B03-provider-fixtures.json').write_bytes(collected.stdout)
    print(collected.stdout.decode())
