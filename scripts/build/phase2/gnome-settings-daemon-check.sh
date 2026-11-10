#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1','GSETTINGS_BACKEND':'memory'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gnome-settings-daemon'],text=True)=='install ok installed 50.1-1+toddy2'
assert subprocess.check_output(prefix+['pkg-config','--modversion','gnome-settings-daemon'],text=True).strip()=='50.1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
w=T/'sources/phase2/work/gnome-settings-daemon-1';expected=json.loads((w/'stage-results.json').read_text())['consumer'];assert not (T/'stage').exists()
for name in ['color','power','media-keys']:
 binary='/usr/libexec/gsd-'+name;libs=subprocess.check_output(prefix+['ldd',binary],env=env,text=True)
 assert 'libgsd.so => /usr/lib/gnome-settings-daemon-50/libgsd.so' in libs
 r=subprocess.run(prefix+[binary,'--help'],env=env,capture_output=True,text=True,timeout=15);assert r.returncode==0 and '--help' in r.stdout
with tempfile.TemporaryDirectory(prefix='toddy-GSD-',dir=T/'tmp') as directory:
 p=Path(directory);p.chmod(0o755);shutil.copyfile('/opt/toddy-build/scripts/build/phase2/gnome-settings-daemon-probe.py',p/'probe.py');shutil.copyfile(w/'compile/data/gschemas.compiled',p/'gschemas.compiled')
 assert hashlib.sha256((p/'gschemas.compiled').read_bytes()).digest()==hashlib.sha256((w/'compile/data/gschemas.compiled').read_bytes()).digest()
 virtual='/tmp/'+p.name;actual=json.loads(subprocess.check_output(['chroot','--userspec=101:101',str(T),'python3',virtual+'/probe.py',virtual],env=env,text=True,timeout=20));assert actual==expected
schema_dir=T/'usr/share/glib-2.0/schemas';assert (schema_dir/'org.gnome.settings-daemon.plugins.power.gschema.xml').exists()
Path('/var/log/toddy/phase2/gnome-settings-daemon-installed-consumer.json').write_text(json.dumps({'scope':'Owned selected Linux Systemd/ALSA/gudev/NM/rfkill/Gcr4/smartcard/colord/USB protection plugin executables/private library/SDK. Actual three installed CLI/private library resolution and UID101 private24schema/memory enum refusal/reset0; stock schema union and real plugin/hardware/audio/power/GNOME acceptance pending. No service manually started by this check.','consumer':actual,'installed_CLI_help':['color','power','media-keys'],'private_libgsd_resolved':True,'stock_schema_cache_pending':True,'optional_omissions':['CUPS','WWAN','XWayland']},indent=2)+'\n')
PY
