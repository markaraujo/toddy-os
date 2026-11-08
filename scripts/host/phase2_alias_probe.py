#!/usr/bin/env python3
"""One native FD-alias qualification with actual parent-lock held/released check."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time
import sys
import phase2_vm
ROOT=phase2_vm.ROOT
if __name__=='__main__':
    assert sys.argv[1:] in ([],['--font-config'],['--private-shm'])
    font_config=bool(sys.argv[1:])
    private_shm=sys.argv[1:]==['--private-shm']
    name='private-shm-probe-1' if private_shm else 'font-config-probe-1' if font_config else 'alias-probe-1'
    evidence='B02-namespace-private-shm.json' if private_shm else 'B02-namespace-font-config.json' if font_config else 'B02-namespace-fd-alias.json'
    files={name:(ROOT/'scripts/build/phase2'/name).read_text() for name in ['namespace_alias_probe.py','isolation_probe.py']}
    prepare='''from pathlib import Path
import fcntl,json,os,subprocess,sys
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
p=Path('/mnt/lfs/sources/phase2/inputs/alias-probe-1');w=Path('/mnt/lfs/sources/phase2/work/alias-probe-1')
assert not p.exists() and not w.exists(),'Inspect existing alias probe; no replay'
p.mkdir();w.mkdir();os.chown(w,101,101)
for name,text in json.load(sys.stdin).items():
 assert name in ['namespace_alias_probe.py','isolation_probe.py'];(p/name).write_text(text)
'''
    prepare=prepare.replace('alias-probe-1',name)
    state=ROOT/'.local/phase2'
    with (state/(name+'-dispatch.log')).open('xb') as log:
        subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(prepare)],input=json.dumps(files).encode(),stdout=log,stderr=subprocess.STDOUT,check=True)
        command='python3 /opt/toddy-build/scripts/build/phase2/job.py alias-probe-1 /mnt/lfs/sources/phase2/inputs/alias-probe-1 /mnt/lfs/sources/phase2/work/alias-probe-1 python3 /src/namespace_alias_probe.py --hold-lock-check'
        command=command.replace('alias-probe-1',name)+(' --font-config' if font_config else '')+(' --private-shm' if private_shm else '')
        process=subprocess.Popen(phase2_vm.ssh_args()+[command],stdout=log,stderr=subprocess.STDOUT)
        try:
            deadline=time.monotonic()+5
            while True:
                ready=subprocess.run(phase2_vm.ssh_args()+['test -f /mnt/lfs/sources/phase2/work/'+name+'/lock-probe-ready'],capture_output=True)
                if ready.returncode==0:break
                assert process.poll() is None and time.monotonic()<deadline,'Reconcile alias job; no replay'
                time.sleep(.05)
            held=subprocess.run(phase2_vm.ssh_args()+['flock -n -E 75 /var/log/toddy/build/build.lock true'],capture_output=True)
            assert held.returncode==75
            if private_shm:
                visible=subprocess.run(phase2_vm.ssh_args()+['test ! -e /dev/shm/toddy-namespace-shm-probe-1'],capture_output=True)
                assert visible.returncode==0,'Private shared memory leaked to parent namespace'
            subprocess.run(phase2_vm.ssh_args()+['touch /mnt/lfs/sources/phase2/work/'+name+'/lock-probe-release'],check=True)
        finally:
            result=process.wait(timeout=15);(state/(name+'-dispatch.exit')).write_text(str(result)+'\n')
        if result:raise SystemExit(result)
    released=subprocess.run(phase2_vm.ssh_args()+['flock -n -E 75 /var/log/toddy/build/build.lock true'],capture_output=True);assert released.returncode==0
    collect="""from pathlib import Path
import json,hashlib
p=Path('/var/log/toddy/phase2/alias-probe-1');assert p.with_suffix('.exit').read_text().strip()=='0'
d=json.loads(p.with_suffix('.log').read_text());d['job']='alias-probe-1';d['harness_sha256']=json.loads(p.with_suffix('.job.json').read_text())['harness_sha256'];print(json.dumps(d,indent=2))
"""
    r=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=collect.replace('alias-probe-1',name).encode(),capture_output=True,check=True)
    d=json.loads(r.stdout);d['parent_lock_held_exit']=75;
    if private_shm:d['parent_shared_memory_visible']=False
    d['parent_lock_released_exit']=0
    d['own_probe_sha256']={name:hashlib.sha256(text.encode()).hexdigest() for name,text in files.items()}
    assert d['harness_sha256']==hashlib.sha256((ROOT/'scripts/build/phase2/isolated.sh').read_bytes()).hexdigest()
    (ROOT/'docs/evidence'/evidence).write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
