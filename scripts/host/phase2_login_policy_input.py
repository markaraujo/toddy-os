#!/usr/bin/env python3
"""Prepare one tiny authored read-only-input client build; never credentials."""
from pathlib import Path
import hashlib,json,shlex,subprocess
import phase2_vm
R=phase2_vm.ROOT
files={n:(R/'scripts/build/phase2'/n).read_text() for n in ['login-password-change.c','login-policy-probe-build.sh']}
code=r'''from pathlib import Path
import fcntl,hashlib,json,os,subprocess
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
s=Path('/mnt/lfs/sources/phase2/inputs/login-policy-probe-1');w=Path('/mnt/lfs/sources/phase2/work/login-policy-probe-1')
assert not s.exists() and not w.exists(),'Reconcile actual input/work; never replay'
assert os.statvfs('/mnt/lfs').f_bavail*os.statvfs('/mnt/lfs').f_frsize>=16*1024**3+1024**2
s.mkdir();w.mkdir();os.chown(w,101,101)
files=FILES
for name,text in files.items():
 p=s/name;p.write_text(text);p.chmod(0o444)
r={'scope':'Authored root-only password-change qualification client source; no actual credentials or operation in build input','files':{n:hashlib.sha256(t.encode()).hexdigest() for n,t in files.items()}}
(s/'toddy-prepared.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
'''.replace('FILES',repr(files))
r=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(code)],capture_output=True,text=True,timeout=30);print(r.stdout);print(r.stderr);assert r.returncode==0
