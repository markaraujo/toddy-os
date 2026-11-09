#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gnome-session'],text=True,env=env)=='install ok installed 50.1-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-gnome-session-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);script=p/'probe.py';script.write_bytes(Path('/opt/toddy-build/scripts/build/phase2/gnome-session-probe.py').read_bytes())
 schemas=p/'schemas';schemas.mkdir();(schemas/'org.gnome.SessionManager.gschema.xml').write_bytes(Path('/mnt/lfs/usr/share/glib-2.0/schemas/org.gnome.SessionManager.gschema.xml').read_bytes())
 subprocess.run(prefix+['glib-compile-schemas','--strict','/tmp/'+p.name+'/schemas'],env=env,check=True)
 r=subprocess.run(prefix+['python3','-B','/tmp/'+p.name+'/probe.py','/','/tmp/'+p.name+'/schemas'],env=env,capture_output=True,text=True,timeout=70,check=True);consumer=json.loads(r.stdout)
Path('/var/log/toddy/phase2/gnome-session-installed-consumer.json').write_text(json.dumps({'scope':'Installed CLI/private schema/session files/package audit; no actual GNOME session/login acceptance','consumer':consumer,'shared_schema_cache_update':'Pending controlled union update before graphical session'},indent=2)+'\n')
PY
