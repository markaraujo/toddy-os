#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'};prefix=['chroot','/mnt/lfs']
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libical'],text=True,env=env)=='install ok installed 4.0.5-1+toddy1'
for pc in ['libical','libical-glib','libicalvcard']:assert subprocess.check_output(prefix+['pkg-config','--modversion',pc],text=True,env=env).strip()=='4.0.5'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip();subprocess.run(prefix+['apt-get','check'],env=env,check=True)
work=Path('/mnt/lfs/sources/phase2/work/libical-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-libical-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);shutil.copyfile(work/'native-probe-3',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((work/'native-probe-3').read_bytes()).digest() and not Path('/mnt/lfs/stage').exists()
 r=subprocess.run(prefix+['/tmp/'+p.name+'/probe'],env=env,capture_output=True,text=True,timeout=20,check=True);consumer=json.loads(r.stdout)
assert consumer==expected
gi_code="import gi,json;gi.require_version('ICalGLib','4.0');from gi.repository import ICalGLib;v=ICalGLib.Time.new_from_string('20261109T120000Z');assert v.get_year()==2026 and v.get_month()==11 and v.get_day()==9;print(json.dumps({'installed_GI_UTC_date':True}))"
r=subprocess.run(prefix+['python3','-c',gi_code],env=env,capture_output=True,text=True,timeout=20,check=True);gi=json.loads(r.stdout)
Path('/var/log/toddy/phase2/libical-installed-consumer.json').write_text(json.dumps({'scope':'Installed UTF8/UTC recurrence/refusal/recovery/GI/SDK/audit; EDS/GNOME calendar UI pending','consumer':consumer,'gi':gi},indent=2)+'\n')
PY
