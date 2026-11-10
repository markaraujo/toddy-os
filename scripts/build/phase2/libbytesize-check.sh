#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile,shlex
T=Path('/mnt/lfs');prefix=['chroot',str(T)]
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libbytesize'],text=True)=='install ok installed 2.12-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip()
subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from qualify_libbytesize import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
with tempfile.TemporaryDirectory(prefix='toddy-libbytesize-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env['HOME']=virtual
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/libbytesize-probe.c',p/'probe.c')
 flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','bytesize'],env=env,text=True))
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; mount -t proc -o nosuid,nodev,noexec proc /mnt/lfs/proc; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-libbytesize']
 launcher="import ctypes,os,sys; assert os.geteuid()==os.getegid()==101; assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0; assert 'CapEff:\\t0000000000000000' in open('/proc/self/status').read(); os.execv(sys.argv[1],sys.argv[1:])"
 base=command+['python3','-c',launcher]
 subprocess.run(base+['/usr/bin/cc',virtual+'/probe.c','-o',virtual+'/probe',*flags],env=env,check=True,timeout=30)
 actual=subprocess.check_output(base+[virtual+'/probe'],env=env,text=True,timeout=15);assert actual==proof['consumer']
 python="from bytesize import Size,InvalidSpecError\nfor cycle in range(2):\n assert int(Size('1 GiB')+Size('512 MiB'))==1610612736\n try:Size('not a size')\n except ValueError as error:assert isinstance(error.args[0],InvalidSpecError)\n else:raise AssertionError('Malformed specification accepted')\n assert int(Size('1 KiB'))==1024\nprint('Python exact size arithmetic/malformed refusal/two recoveries')"
 binding=subprocess.check_output(base+['/usr/bin/python3','-c',python],env=env,text=True,timeout=10);assert binding==proof['python_consumer']
 cli=subprocess.check_output(base+['/usr/bin/bscalc','-b','1 GiB + 512 MiB'],env=env,text=True,stdin=subprocess.DEVNULL,timeout=10);assert cli==proof['CLI']
 refusal=subprocess.run(base+['/usr/bin/bscalc','-b','__import__("sys").exit(0)'],env=env,text=True,stdin=subprocess.DEVNULL,capture_output=True,timeout=10)
 assert refusal.returncode==1 and 'Error while parsing expression:' in refusal.stdout
 recovery=subprocess.check_output(base+['/usr/bin/bscalc','-b','1 KiB'],env=env,text=True,stdin=subprocess.DEVNULL,timeout=10);assert recovery=='1024 B\n'
library=subprocess.check_output(prefix+['ldd','/usr/lib/libbytesize.so.1'],env=env,text=True);assert 'not found' not in library
assert subprocess.check_output(prefix+['pkg-config','--modversion','bytesize'],env=env,text=True).strip()=='2.12'
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/libbytesize-installed-consumer.json').write_text(json.dumps({'scope':'Owned frozen libbytesize2.12 installed shared C/Python/CLI size arithmetic, exact big integer/overflow/invalid/zero-divisor/two recoveries, expression parse refusal/recovery, UID101/NNP/caps0/private-device/no-route, exact stage bytes/ABI/PC/APT. Original selected76passing/3explicit locale skips; optional translation-canary pending. No device/disk/daemon/UDisks/Settings GUI/hardware acceptance.','C_consumer':actual,'Python_consumer':binding,'CLI':cli,'CLI_refusal_exit':refusal.returncode,'CLI_recovery':recovery,'stage_files':len(proof['stage_sha256']),'shared_library_resolution':True,'physical_machine_tested':False},indent=2)+'\n')
PY
