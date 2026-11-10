#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','editorconfig'],text=True)=='install ok installed 0.12.11-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_editorconfig import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
with tempfile.TemporaryDirectory(prefix='toddy-editorconfig-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env['HOME']=virtual
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/editorconfig-probe.py',p/'probe.py')
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-editorconfig']
 launcher="import ctypes,os,runpy,sys; assert os.geteuid()==os.getegid()==101; assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0; sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')"
 actual=json.loads(subprocess.check_output(command+['python3','-c',launcher,virtual+'/probe.py','/',virtual+'/consumer'],env=env,text=True,timeout=45));assert actual==proof['consumer']
libs=subprocess.check_output(prefix+['ldd','/usr/bin/editorconfig'],env=env,text=True);assert 'libeditorconfig.so.0 => /usr/lib/libeditorconfig.so.0' in libs and 'not found' not in libs
s=os.statvfs('/mnt/lfs');assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/editorconfig-installed-consumer.json').write_text(json.dumps({'scope':'Actual owned installed EditorConfig C API/CLI, layered UTF8 settings, UID101/NoNewPrivs/private devices/no external route, Relative path/malformed configuration refusal/input retention/recovery, all staged bytes retained/APT0. Builder kernel; no editor/GUI/general parser-security acceptance.','consumer':actual,'installed_stage_files_identical':len(proof['stage_sha256']),'shared_library_resolution':True},indent=2)+'\n')
PY
