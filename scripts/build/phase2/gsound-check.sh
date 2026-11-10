#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile,shlex
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gsound'],text=True)=='install ok installed 1.0.3-1+toddy2'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_gsound import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
with tempfile.TemporaryDirectory(prefix='toddy-gsound-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env['HOME']=virtual
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/gsound-probe.c',p/'probe.c')
 flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','gsound','gio-2.0'],env=env,text=True))
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-gsound']
 launcher="import ctypes,os,sys; assert os.geteuid()==os.getegid()==101; assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0; os.execv(sys.argv[1],sys.argv[1:])"
 subprocess.run(command+['python3','-c',launcher,'/usr/bin/cc',virtual+'/probe.c','-o',virtual+'/probe',*flags],env=env,check=True,timeout=30)
 actual=subprocess.check_output(command+['python3','-c',launcher,virtual+'/probe'],env=env,text=True,timeout=15)
 assert actual=='GSound null backend/Unicode properties/disabled refusal/two recoveries; no audible output\n'
 gi="import gi;gi.require_version('GSound','1.0');from gi.repository import GSound;assert GSound.Context.__gtype__.name=='GSoundContext';print('GSound1 GI type available')"
 introspection=subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/python3','-c',gi],env=env,text=True,timeout=15)
 assert introspection.strip()=='GSound1 GI type available'
 help=subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/gsound-play','--help'],env=env,text=True,timeout=15);assert help==proof['consumer']['help']
 empty=subprocess.run(command+['python3','-c',launcher,'/usr/bin/gsound-play'],env=env,text=True,capture_output=True,timeout=15);assert empty.returncode==1 and 'No event id or file specified.' in empty.stdout
libs=subprocess.check_output(prefix+['ldd','/usr/lib/libgsound.so.0'],env=env,text=True);assert 'not found' not in libs and 'libcanberra.so.0 => /usr/lib/libcanberra.so.0' in libs
assert subprocess.check_output(prefix+['pkg-config','--modversion','gsound'],env=env,text=True).strip()=='1.0.3'
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/gsound-installed-consumer.json').write_text(json.dumps({'scope':'Owned installed GSound1.0.3 shared/GI/Vala tools, UID101/NNP/private-dev/no-route null backend only, Unicode properties/disabled refusal/two recoveries/local GI type/CLI help-empty refusal/APT0. No physical/audible/notification/Bluetooth/Settings GUI acceptance.','C_consumer':actual,'GI_consumer':introspection,'installed_stage_files_identical':len(proof['stage_sha256']),'shared_library_resolution':True,'audible_output_tested':False},indent=2)+'\n')
PY
