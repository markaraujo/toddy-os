#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile,shlex
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','colord-gtk'],text=True)=='install ok installed 0.3.1-1+toddy2'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_colord_gtk import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
consumers={}
with tempfile.TemporaryDirectory(prefix='toddy-colord-gtk-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env['HOME']=virtual
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/colord-gtk-probe.c',p/'probe.c')
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-colord-gtk']
 launcher="import ctypes,os,sys; assert os.geteuid()==os.getegid()==101; assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0; os.execv(sys.argv[1],sys.argv[1:])"
 for pc in ['colord-gtk','colord-gtk4']:
  flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs',pc,'gio-2.0'],env=env,text=True))
  subprocess.run(command+['python3','-c',launcher,'/usr/bin/cc',virtual+'/probe.c','-o',virtual+'/'+pc+'-probe',*flags],env=env,check=True,timeout=30)
  consumers[pc]=subprocess.check_output(command+['python3','-c',launcher,virtual+'/'+pc+'-probe'],env=env,text=True,timeout=15);assert consumers[pc]==proof['consumer'][pc]
  assert subprocess.check_output(prefix+['pkg-config','--modversion',pc],env=env,text=True).strip()=='0.3.1'
 for lib in ['libcolord-gtk.so.1','libcolord-gtk4.so.1']:
  libs=subprocess.check_output(prefix+['ldd','/usr/lib/'+lib],env=env,text=True);assert 'not found' not in libs
 gi="import gi;gi.require_version('ColordGtk','1.0');from gi.repository import ColordGtk;\nfor cycle in range(2):\n w=ColordGtk.Window.new();assert w.get_last_profile() is None\nprint('ColordGtk GTK3 GI local empty-profile/two fresh cycles')"
 introspection=subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/python3','-c',gi],env=env,text=True,timeout=15);assert introspection.strip()=='ColordGtk GTK3 GI local empty-profile/two fresh cycles'
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/colord-gtk-installed-consumer.json').write_text(json.dumps({'scope':'Owned colord-gtk0.3.1 GTK3+GTK4 ABI and GTK3 GI only; optional Vala unavailable; actual UID101/NNP/private-device/no-route separate C local non-widget GObjects/empty-profile/two cycles, GTK3 GI and shared ABI/APT. Original display tests unexecuted. No widget/profile mapping/color calibration/daemon/Settings GUI/physical acceptance.','C_consumers':consumers,'GTK3_GI_consumer':introspection,'installed_stage_files_identical':len(proof['stage_sha256']),'shared_library_resolution':True,'original_display_suite_pending':True,'physical_monitor_tested':False},indent=2)+'\n')
PY
