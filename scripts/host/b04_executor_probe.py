#!/usr/bin/env python3
"""One guarded synthetic-root native executor probe; never installed/host config."""
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import phase2_vm
ROOT=phase2_vm.ROOT
NAME=sys.argv[1] if len(sys.argv)>1 else 'executor-ipc-1'
assert re.fullmatch(r'executor-ipc-[1-9][0-9]*',NAME)
FILES=['runtime/executor/'+n for n in ['store.py','operations.py','service.py','policy.py','native_probe.py',
       'native_backends.py','package_probe.py','package_debug_launcher.py','command_child.py','linux_identity.py','dbus-probe.conf','io.github.markaraujo.Toddy.Executor1.xml']]
HARNESS='scripts/build/phase2/executor-probe.sh'
if __name__=='__main__':
    payload={n:(ROOT/n).read_text() for n in FILES+[HARNESS]}
    remote='''from pathlib import Path
import fcntl,hashlib,json,os,socket,subprocess,sys,time
assert socket.gethostname()=='toddy-builder' and os.getuid()==0
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
p=Path('/mnt/lfs/sources/phase2/inputs/executor-ipc-1');w=Path('/mnt/lfs/sources/phase2/work/executor-ipc-1')
prefix=Path('/var/log/toddy/phase2/executor-ipc-1')
assert not p.exists() and not w.exists() and not prefix.with_suffix('.job.json').exists(), 'Inspect existing job; no replay'
p.mkdir(mode=0o755);w.mkdir(mode=0o755)
payload=json.load(sys.stdin)
for name,text in payload.items():
    assert name.startswith(('runtime/executor/','runtime/broker/','scripts/build/phase2/')) and '..' not in name
    target=p/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
record={'pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'started_unix':time.time(),
        'input_sha256':{n:hashlib.sha256(v.encode()).hexdigest() for n,v in payload.items()}}
prefix.with_suffix('.job.json').write_text(json.dumps(record,indent=2))
# The dedicated harness takes the same lock after preparation releases it.
fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
with prefix.with_suffix('.log').open('xb') as log:
    result=subprocess.run(['bash',str(p/'scripts/build/phase2/executor-probe.sh'),str(p),str(w)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
part=prefix.with_suffix('.exit.part');part.write_text(str(result.returncode)+'\\n');part.replace(prefix.with_suffix('.exit'))
raise SystemExit(result.returncode)
'''.replace('executor-ipc-1',NAME)
    state=ROOT/'.local/phase2'
    with (state/(NAME+'-dispatch.log')).open('xb') as log:
        result=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(remote)],input=json.dumps(payload).encode(),stdout=log,stderr=subprocess.STDOUT)
        (state/(NAME+'-dispatch.exit')).write_text(str(result.returncode)+'\n')
    if result.returncode:raise SystemExit(result.returncode)
    collect='''from pathlib import Path
import json
p=Path('/var/log/toddy/phase2/executor-ipc-1')
assert p.with_suffix('.exit').read_text().strip()=='0'
d=json.loads(p.with_suffix('.log').read_text());d['job']='executor-ipc-1';d['own_input_sha256']=json.loads(p.with_suffix('.job.json').read_text())['input_sha256']
print(json.dumps(d,indent=2))
'''.replace('executor-ipc-1',NAME)
    result=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=collect.encode(),capture_output=True,check=True)
    d=json.loads(result.stdout)
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==sha for n,sha in d['own_input_sha256'].items())
    (ROOT/'docs/evidence/B04-native-executor.json').write_bytes(result.stdout);print(result.stdout.decode())
