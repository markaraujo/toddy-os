#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,subprocess,sys,tempfile
T=Path('/mnt/lfs');env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','GSETTINGS_BACKEND':'memory'};prefix=['chroot',str(T)]
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gnome-text-editor'],text=True)=='install ok installed 50.1-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_gnome_text_editor import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
with tempfile.TemporaryDirectory(prefix='toddy-editor-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env['HOME']=virtual
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-editor']
 launcher="import ctypes,os,subprocess; assert os.geteuid()==os.getegid()==101; assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0; r=subprocess.run(['/usr/bin/gnome-text-editor','--version'],check=True,text=True,capture_output=True);print(r.stdout,end='')"
 version=subprocess.check_output(command+['python3','-c',launcher],env=env,text=True,timeout=30);assert version==proof['consumer']['version']
 code="from gi.repository import Gio; import json; s=Gio.SettingsSchemaSource.get_default();print(json.dumps({'default_editor_schema_available':s.lookup('org.gnome.TextEditor',True) is not None}))"
 schemas=json.loads(subprocess.check_output(command+['python3','-c',code],env=env,text=True,timeout=15))
 libs=subprocess.check_output(prefix+['ldd','/usr/bin/gnome-text-editor'],env=env,text=True);assert 'libspelling-1.so.2 => /usr/lib/libspelling-1.so.2' in libs and 'libeditorconfig.so.0 => /usr/lib/libeditorconfig.so.0' in libs and 'not found' not in libs
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/gnome-text-editor-installed-consumer.json').write_text(json.dumps({'scope':'Owned native editor package/payload/APT/version execution UID101/NoNewPrivs/private-dev/no-route and real shared-library resolution only. Shared schema/icon/desktop cache integration and graphical open/edit/save/recovery/focus remain pending; unavailable default schema is recorded, never a GUI pass.','version':version,'installed_stage_regular_files_identical':len(proof['stage_sha256']),'shared_library_resolution':True,**schemas,'graphical_editor_tested':False},indent=2)+'\n')
PY
