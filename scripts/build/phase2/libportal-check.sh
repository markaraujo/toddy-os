#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libportal'],text=True)=='install ok installed 0.9.1-1+toddy1'
for n in ['libportal','libportal-gtk3','libportal-gtk4']:assert subprocess.check_output(prefix+['pkg-config','--modversion',n],text=True).strip()=='0.9.1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
r=json.loads((T/'sources/phase2/work/libportal-1/stage-results.json').read_text());assert not (T/'stage').exists()
with tempfile.TemporaryDirectory(prefix='toddy-libportal-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);shutil.copyfile(T/'sources/phase2/work/libportal-1/native-probe',p/'native-probe');(p/'native-probe').chmod(0o755);virtual='/tmp/'+p.name
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-libportal']
 actual=json.loads(subprocess.check_output(command+['dbus-run-session','--',virtual+'/native-probe'],env=env,text=True,timeout=30));assert actual==r['consumer']
 gi=[]
 for v in ['3','4']:
  code="import gi,ctypes,json;v="+repr(v)+";gi.require_version('Gtk',v+'.0');gi.require_version('Xdp','1.0');gi.require_version('XdpGtk'+v,'1.0');from gi.repository import Xdp;m=__import__('gi.repository',fromlist=['XdpGtk'+v]);namespace=getattr(m,'XdpGtk'+v);assert Xdp.Portal.__gtype__.name=='XdpPortal';lib=ctypes.CDLL('/usr/lib/libportal-gtk'+v+'.so');assert getattr(lib,'xdp_parent_new_gtk');print(json.dumps({'namespace':'XdpGtk'+v+'1.0','base_GI_type':'XdpPortal','GTK_backend_symbol_loaded':True,'widget_or_parent_export_tested':False}))"
  gi.append(json.loads(subprocess.check_output(command+['python3','-c',code],env=env,text=True,timeout=15)))
 assert gi==r['GI_consumers']
 libs=subprocess.check_output(prefix+['ldd',virtual+'/native-probe'],env=env,text=True);assert 'libportal.so.1 => /usr/lib/libportal.so.1' in libs and 'not found' not in libs
Path('/var/log/toddy/phase2/libportal-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed UID101/private device/no-route/private session bus base libportal constructor/context/two release cycles and separate GTK3/4 GI/shared symbol/pkg-config/APT0. Original61private mock-portal pytest cases passed, not actual GNOME backend/service/permission/input/capture/widget acceptance. No grant or policy mutated.','consumer':actual,'GI_consumers':gi,'shared_library_resolution':True,'original_mock_cases':61,'actual_desktop_portal_or_permission_tested':False},indent=2)+'\n')
PY
