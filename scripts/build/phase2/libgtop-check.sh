#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile,shlex
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libgtop'],text=True)=='install ok installed 2.41.3-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_libgtop import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():
 if relative!='usr/share/info/dir':assert digest(T/relative)==sha
assert 'libgtop' in (T/'usr/share/info/dir').read_text()
for name in ['libgtop_server2','libgtop_daemon2']:
 p=T/'usr/libexec'/name;assert p.stat().st_uid==p.stat().st_gid==0 and p.stat().st_mode&0o7777==0o755
with tempfile.TemporaryDirectory(prefix='toddy-libgtop-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env['HOME']=virtual
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/libgtop-probe.c',p/'probe.c')
 flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','libgtop-2.0'],env=env,text=True))
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; mount -t proc -o nosuid,nodev,noexec proc /mnt/lfs/proc; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-libgtop']
 launcher="import ctypes,os,sys; assert os.geteuid()==os.getegid()==101; assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0; os.execv(sys.argv[1],sys.argv[1:])"
 subprocess.run(command+['python3','-c',launcher,'/usr/bin/cc',virtual+'/probe.c','-o',virtual+'/probe',*flags],env=env,check=True,timeout=30)
 actual=subprocess.check_output(command+['python3','-c',launcher,virtual+'/probe'],env=env,text=True,timeout=15);assert actual==proof['consumer']
 gi="import gi;gi.require_version('GTop','2.0');from gi.repository import GTop;assert callable(GTop.glibtop_get_mem);print('GTop2 GI namespace and memory function available; not a GI statistics call')"
 introspection=subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/python3','-c',gi],env=env,text=True,timeout=15);assert introspection.strip()=='GTop2 GI namespace and memory function available; not a GI statistics call'
for relative in proof['stage_sha256']:
 if (T/relative).open('rb').read(4)==b'\x7fELF':
  libs=subprocess.check_output(prefix+['ldd','/'+relative],env=env,text=True);assert 'not found' not in libs
assert subprocess.check_output(prefix+['pkg-config','--modversion','libgtop-2.0'],env=env,text=True).strip()=='2.41.3'
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/libgtop-installed-consumer.json').write_text(json.dumps({'scope':'Owned libgtop2.41.3 shared/GI/0755 helper payload. Actual UID101/NNP/private-proc/private-device/no-route direct C memory/uptime/own-process/missingPID refusal/two recoveries, GI namespace/function availability only, ABI/PC/APT and Info registration. No original suite exists. Helpers not activated or granted setuid; no remote/helper protocol/other-user process/Settings GUI/desktop-resource/physical acceptance.','C_consumer':actual,'GI_metadata_consumer':introspection,'installed_stage_regular_files':len(proof['stage_sha256']),'shared_generated_info_index':'Own staged index excluded from byte comparison; native shared libgtop registration verified','shared_library_resolution':True,'helper_modes':'root:root0755, no setuid/setgid','physical_machine_tested':False},indent=2)+'\n')
PY
