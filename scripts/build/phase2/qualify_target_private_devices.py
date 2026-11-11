"""Qualify explicit private device bindings without touching unbooted target devices."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import stat
import subprocess

TARGET=Path('/mnt/lfs')
LOG=Path('/var/log/toddy/phase2')

CHILD=r'''
from pathlib import Path
import os,subprocess,sys
assert os.getpid()==1 and os.geteuid()==0
subprocess.run(['mount','--make-rprivate','/'],check=True)
subprocess.run(['mount','--bind','/mnt/lfs','/mnt/lfs'],check=True)
subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev','/mnt/lfs'],check=True)
subprocess.run(['mount','-t','tmpfs','-o','size=1M,mode=0755,nosuid,noexec','toddy-private-devices','/mnt/lfs/dev'],check=True)
for name in ['null','zero','random','urandom']:
 p=Path('/mnt/lfs/dev')/name;p.touch()
 subprocess.run(['mount','--bind','/dev/'+name,str(p)],check=True)
for name,target in [('fd','/proc/self/fd'),('stdin','/proc/self/fd/0'),('stdout','/proc/self/fd/1'),('stderr','/proc/self/fd/2')]:
 (Path('/mnt/lfs/dev')/name).symlink_to(target)
subprocess.run(['mount','-t','proc','-o','nosuid,nodev,noexec','proc','/mnt/lfs/proc'],check=True)
usercode=sys.argv[1]
result=subprocess.run(['chroot','--userspec=101:101','--groups=101','/mnt/lfs','python3','-B','-c',usercode],env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'},close_fds=True)
sys.exit(result.returncode)
'''
USER=r'''
from pathlib import Path
import ctypes,errno,json,os,socket,stat
assert os.geteuid()==os.getegid()==101 and set(os.getgroups())<={101}
assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0
status=Path('/proc/self/status').read_text().splitlines()
assert all(next(r for r in status if r.startswith(k)).split()[1]=='0000000000000000' for k in ['CapEff:','CapPrm:'])
assert next(r for r in status if r.startswith('NoNewPrivs:')).split()[1]=='1'
rows=[]
for name,identity in [('null',(1,3)),('zero',(1,5)),('random',(1,8)),('urandom',(1,9))]:
 p=Path('/dev')/name;s=p.stat();assert stat.S_ISCHR(s.st_mode) and (os.major(s.st_rdev),os.minor(s.st_rdev))==identity
 rows.append({'path':str(p),'character_device':True,'major':identity[0],'minor':identity[1]})
with open('/dev/null','wb') as f:assert f.write(b'private device write control')==28
with open('/dev/null','rb') as f:assert f.read(1)==b''
with open('/dev/zero','rb') as f:assert f.read(16)==bytes(16)
for n in ['random','urandom']:
 with open('/dev/'+n,'rb') as f:assert len(f.read(16))==16
try:Path('/etc/toddy-private-device-negative').write_bytes(b'never written')
except OSError as e:assert e.errno==errno.EROFS
else:raise AssertionError('Target root unexpectedly writable')
with socket.socket() as s:
 try:s.connect(('192.0.2.1',9))
 except OSError as e:assert e.errno==errno.ENETUNREACH
 else:raise AssertionError('External network unexpectedly reachable')
print(json.dumps({'UID':101,'NoNewPrivs':True,'effective_permitted_capabilities_zero':True,'devices':rows,'null_write_read':True,'zero_and_rng_read':True,'target_root_write_denied':True,'external_network_unreachable':True}))
'''


def identity(path):
    if not path.exists() and not path.is_symlink():return {"exists":False}
    s=path.lstat()
    return {'inode':s.st_ino,'device':s.st_dev,'mode':s.st_mode,'uid':s.st_uid,'gid':s.st_gid,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'rdev':s.st_rdev}


def main():
    assert os.geteuid()==0
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    receipt=LOG/'private-target-device-profile-1.json'
    log=LOG/'private-target-device-profile-1.log'
    assert not receipt.exists() and not log.exists(),'Inspect real prior result; never replay'
    before={n:identity(TARGET/'dev'/n) for n in ['null','zero','random','urandom']}
    state={'state':'qualification-intended','scope':'Independent private device namespace only; no LocalSearch helper/functional/native retry, no global device mutation or permission relaxation','boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'target_devices_before':before,'producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    receipt.write_text(json.dumps(state,indent=2)+'\n')
    result=subprocess.run(['unshare','--mount','--pid','--net','--ipc','--fork','--kill-child=SIGKILL','python3','-B','-c',CHILD,USER],capture_output=True,text=True,timeout=30,close_fds=True)
    log.write_text(result.stdout+result.stderr)
    after={n:identity(TARGET/'dev'/n) for n in before}
    state.update(exit=result.returncode,target_devices_after=after,target_devices_unchanged=before==after)
    state['state']='qualified' if result.returncode==0 and before==after else 'failed-preserved'
    if result.returncode==0:state['actual']=json.loads(result.stdout)
    receipt.write_text(json.dumps(state,indent=2)+'\n')
    assert state['state']=='qualified',result.stderr
    print(json.dumps(state))


if __name__=='__main__':main()
