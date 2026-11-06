#!/usr/bin/env python3
"""Exercise the native minimal runtime's root switch in disposable namespaces.

Uses two private tmpfs roots in the designated builder; never boots an image.
"""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
module=base64.b64encode(Path('scripts/build/h10/initramfs_runtime.py').read_bytes()).decode()
inner=r'''import base64,json,os,stat,subprocess
from pathlib import Path
assert os.getpid()==1,'Private PID namespace is mandatory'
root=Path('/mnt/lfs');base=Path(BASE)
assert base.resolve()==base and base.parent==root/'tmp'
ns={'__name__':'private_runtime_probe','__file__':'/opt/toddy-build/scripts/build/h10/initramfs_runtime.py'}
exec(compile(base64.b64decode(MODULE),ns['__file__'],'exec'),ns)
def run(*args):subprocess.run(args,check=True)
initial_memory=base/'initial-memory';final_memory=base/'final-memory'
for p in (initial_memory,final_memory):
 p.mkdir();run('mount','-t','tmpfs','-o','size=128m,mode=0755','tmpfs',str(p))
initial=initial_memory/'runtime';final=final_memory/'runtime'
for stage in (initial,final):ns['stage_runtime'](root,stage,Path('/var/log/toddy/packages'))
assert initial.stat().st_dev!=final.stat().st_dev
run('mount','--bind',str(initial),str(initial))
run('mount','--bind',str(final),str(initial/'newroot'))
run('mount','-t','tmpfs','-o','size=1m,mode=0755','tmpfs',str(initial/'run'))
run('mount','-t','tmpfs','-o','size=1m,mode=0755','tmpfs',str(initial/'dev'))
for name,mode,device in [('console',0o600,(5,1)),('null',0o666,(1,3))]:
 p=initial/'dev'/name;os.mknod(p,stat.S_IFCHR|mode,os.makedev(*device));p.chmod(mode)
(initial/'old-root-marker').write_text('temporary initial root\n')
(final/'final-root-marker').write_text('private final root\n')
start='''+repr('''#!/bin/bash
set -euo pipefail
[[ $$ == 1 ]]
[[ -f /old-root-marker && -f /newroot/final-root-marker ]]
mount -t proc -o nosuid,nodev,noexec proc /proc
mount -t sysfs -o ro,nosuid,nodev,noexec sysfs /sys
printf 'survives switch_root\n' > /run/toddy-marker
printf 'INITIAL_RUNTIME_PID1\n'
exec switch_root /newroot /bin/bash /verify-root.sh
''')+r'''
verify='''+repr('''#!/bin/bash
set -euo pipefail
[[ $$ == 1 ]]
[[ -f /final-root-marker && ! -e /old-root-marker && ! -e /newroot/final-root-marker ]]
[[ -c /dev/null && -c /dev/console ]]
[[ $(cat /run/toddy-marker) == 'survives switch_root' ]]
[[ $(readlink /proc/1/root) == / ]]
[[ -d /sys/kernel ]]
[[ ! -e /sources && ! -e /tools && ! -e /etc/shadow ]]
printf 'discarded\n' > /dev/null
for point in /dev /proc /sys /run; do
 found=0
 while read -r id parent device root target options rest; do
  if [[ $target == "$point" ]]; then found=1;break;fi
 done < /proc/self/mountinfo
 [[ $found == 1 ]]
done
printf 'NATIVE_SWITCH_ROOT_PROBE_OK pid=1 mounts=dev,proc,sys,run\n'
''')+r'''
(initial/'init').write_text(start);(initial/'init').chmod(0o755)
(final/'verify-root.sh').write_text(verify);(final/'verify-root.sh').chmod(0o755)
os.execve('/usr/sbin/chroot',['chroot',str(initial),'/bin/bash','/init'],{'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C'})
'''
outer=r'''from pathlib import Path
import base64,json,subprocess,tempfile,shutil,os
root=Path('/mnt/lfs');base=Path(tempfile.mkdtemp(prefix='toddy-switch-root-',dir=root/'tmp'))
print('SWITCH_ROOT_FIXTURE '+str(base),flush=True)
script=base64.b64decode(INNER).decode().replace('BASE',repr(str(base))).replace('MODULE',repr(MODULE))
r=subprocess.run(['unshare','--mount','--pid','--fork','--kill-child=KILL','--propagation','private','python3','-'],input=script,text=True,capture_output=True,timeout=60,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
report={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'builder_kernel':os.uname().release,'native_kernel_boot':False,'iso_boot':False,'private_pid_and_mount_namespaces':True,'fixture':str(base)}
print(json.dumps(report,indent=2))
assert r.returncode==0 and 'NATIVE_SWITCH_ROOT_PROBE_OK pid=1 mounts=dev,proc,sys,run' in r.stdout
# The namespace exited; its tmpfs contents and mounts cannot remain here.
assert all(not any((base/name).iterdir()) for name in ('initial-memory','final-memory'))
shutil.rmtree(base)
'''
outer=outer.replace('INNER',repr(base64.b64encode(inner.encode()).decode())).replace('MODULE)',repr(module)+')')
r=subprocess.run(['python3','scripts/host/vm.py','ssh','source /opt/toddy-build/scripts/build/target.sh; guard_target && python3 -'],input=outer,text=True,capture_output=True)
p=Path('.local/logs/h10-native-switch-root-probe.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2)+'\n')
print(r.stdout,r.stderr);print('exit',r.returncode,'SHA256',hashlib.sha256(p.read_bytes()).hexdigest());r.check_returncode()
