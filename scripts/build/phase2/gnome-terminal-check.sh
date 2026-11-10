#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gnome-terminal'],text=True)=='install ok installed 3.60.0-1+toddy2'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
r=json.loads((T/'sources/phase2/work/gnome-terminal-1/stage-results.json').read_text())
with tempfile.TemporaryDirectory(prefix='toddy-gnome-terminal-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);shutil.copyfile('/opt/toddy-build/scripts/build/phase2/gnome-terminal-probe.py',p/'probe.py');virtual='/tmp/'+p.name
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-terminal']
 actual=json.loads(subprocess.check_output(command+['python3',virtual+'/probe.py','/',virtual+'/consumer'],env=env,text=True,timeout=90));assert actual==r['consumer']
 bad=subprocess.run(command+['/usr/bin/gnome-terminal','--toddy-invalid-option'],env=env,capture_output=True,text=True,timeout=15);assert bad.returncode!=0 and 'unknown option' in bad.stderr.lower() and '--toddy-invalid-option' in bad.stderr
 code="from gi.repository import Gio; s=Gio.SettingsSchemaSource.new_from_directory('/usr/lib/gnome-terminal',None,False);ids=['org.gnome.system.proxy','org.gnome.system.proxy.http','org.gnome.system.proxy.https','org.gnome.system.proxy.ftp','org.gnome.system.proxy.socks'];assert all(s.lookup(n,False).get_path().startswith('/org/gnome/system/proxy/') for n in ids);print('five corrected paths')"
 assert subprocess.check_output(command+['python3','-c',code],env=env,text=True,timeout=15).strip()=='five corrected paths'
 libs=subprocess.check_output(prefix+['ldd','/usr/libexec/gnome-terminal-server'],env=env,text=True);assert 'libvte-2.91.so.0 => /usr/lib/libvte-2.91.so.0' in libs and 'libhandy-1.so.0 => /usr/lib/libhandy-1.so.0' in libs and 'not found' not in libs
 depends=subprocess.check_output(prefix+['dpkg-query','-W','-f=${Depends}','gnome-terminal'],text=True);assert 'libxslt' not in depends and 'fmt ' not in depends and 'fast-float' not in depends
assert not (T/'usr/share/metainfo/org.gnome.Terminal.Nautilus.metainfo.xml').exists()
Path('/var/log/toddy/phase2/gnome-terminal-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed UID101/no-route client3.60.0/exact unknown-option error/private DConf Unicode/navy typed profile/malformed boolean refusal/persistence across two buses/reset declared defaults/system font preservation; five corrected reference schema paths/shared VTE+libhandy/APT0. No GUI/window/focus/PTY/desktop/login acceptance. Stock schema cache integration remains pending.','consumer':actual,'shared_library_resolution':True,'five_reference_schema_paths_corrected':True,'runtime_does_not_force_build_SDKs':True,'unbuilt_Nautilus_addon_not_advertised':True},indent=2)+'\n')
PY
