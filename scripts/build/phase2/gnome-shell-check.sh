#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1','GSETTINGS_BACKEND':'memory','LD_LIBRARY_PATH':'/usr/lib/gnome-shell:/usr/lib/mutter-18','GI_TYPELIB_PATH':'/usr/lib/gnome-shell:/usr/lib/mutter-18'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gnome-shell'],text=True)=='install ok installed 50.4-1+toddy1'
assert subprocess.check_output(prefix+['gnome-shell','--version'],env=env,text=True).strip()=='GNOME Shell 50.4'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
w=T/'sources/phase2/work/gnome-shell-1';accepted=json.loads((w/'stage-results.json').read_text())['consumer']
assert not (T/'usr/share/applications/org.gnome.Shell.Extensions.desktop').exists()
with tempfile.TemporaryDirectory(prefix='toddy-shell-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);src=p/'source/js/misc';src.mkdir(parents=True)
 original=T/'sources/phase2/inputs/gnome-shell-50.4/js/misc/params.js'
 assert hashlib.sha256(original.read_bytes()).hexdigest()==accepted['params_source_sha256']
 shutil.copyfile(original,src/'params.js');shutil.copyfile('/opt/toddy-build/scripts/build/phase2/gnome-shell-probe.py',p/'probe.py')
 virtual='/tmp/'+p.name
 actual=json.loads(subprocess.check_output(['chroot','--userspec=101:101',str(T),'python3',virtual+'/probe.py',virtual+'/source','/',virtual],env=env,text=True,timeout=30))
 assert actual==accepted
Path('/var/log/toddy/phase2/gnome-shell-installed-consumer.json').write_text(json.dumps({'scope':'Actual UID101 installed Shell/St GI, source JS parameters, private schema memory roundtrip/type detection/reset, CLI/package audit only. Source Params fixture copied with accepted hash; no fake display/login. Stock cache and native graphical session/original display suite remain pending.','consumer':actual,'installed_CLI':'GNOME Shell 50.4','stock_schema_cache_pending':True,'real_GNOME_login_UI_tested':False,'disabled_app_launcher_absent':True},indent=2)+'\n')
PY
