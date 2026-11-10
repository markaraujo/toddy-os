#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile,shlex
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gnome-bluetooth'],text=True)=='install ok installed 47.2-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_gnome_bluetooth import qualify,digest
proof=qualify(Path('/opt/toddy-build'))
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
with tempfile.TemporaryDirectory(prefix='toddy-gnome-bluetooth-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name;env['HOME']=virtual
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/gnome-bluetooth-probe.c',p/'probe.c')
 flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','gnome-bluetooth-ui-3.0','gio-2.0','gtk4'],env=env,text=True))
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-gnome-bluetooth']
 launcher="import ctypes,os,sys; assert os.geteuid()==os.getegid()==101; assert ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0; os.execv(sys.argv[1],sys.argv[1:])"
 subprocess.run(command+['python3','-c',launcher,'/usr/bin/cc',virtual+'/probe.c','-o',virtual+'/probe',*flags],env=env,check=True,timeout=30)
 actual=subprocess.check_output(command+['python3','-c',launcher,virtual+'/probe'],env=env,text=True,timeout=15)
 assert actual=='Installed BluetoothSettingsWidget C SDK/type ABI only; no widget instantiated\n'
 gi="import gi;gi.require_version('GnomeBluetooth','3.0');from gi.repository import GnomeBluetooth as B;assert B.verify_address('11:22:33:44:55:66');assert B.verify_address('11:22:33:44:55:FF');assert not any(B.verify_address(x) for x in ['11:22:33:44:55','11:22:33:44:55:6','foobar']);assert B.class_to_type(268)==B.Type.COMPUTER;print('GnomeBluetooth3 GI address validation/classification only')"
 introspection=subprocess.check_output(command+['python3','-c',launcher,'/usr/bin/python3','-c',gi],env=env,text=True,timeout=15)
 assert introspection.strip()=='GnomeBluetooth3 GI address validation/classification only'
libs=subprocess.check_output(prefix+['ldd','/usr/lib/libgnome-bluetooth-ui-3.0.so.13'],env=env,text=True);assert 'not found' not in libs
for name in ['libgtk-4.so.1','libgsound.so.0','libnotify.so.4']:assert name+' => /usr/lib/'+name in libs
assert subprocess.check_output(prefix+['pkg-config','--modversion','gnome-bluetooth-3.0','gnome-bluetooth-ui-3.0'],env=env,text=True).splitlines()==['47.2','47.2']
s=os.statvfs(T);assert s.f_bavail*s.f_frsize>=16*1024**3
Path('/var/log/toddy/phase2/gnome-bluetooth-installed-consumer.json').write_text(json.dumps({'scope':'Owned GNOME Bluetooth47.2 core/UI/GI/sendto payload; UID101/NNP/private-dev/no-route C UI header/type query only (no widget instantiated), real installed core GI address validation/classification/ABI/APT0. Original2programs5cases reused;15private-bus integration programs compiled/deferred. No real adapter/pairing/transfer/Bluetooth GUI/Settings/physical acceptance.','C_consumer':actual,'GI_consumer':introspection,'installed_stage_files_identical':len(proof['stage_sha256']),'shared_library_resolution':True,'widget_instantiated':False,'physical_Bluetooth_tested':False},indent=2)+'\n')
PY
