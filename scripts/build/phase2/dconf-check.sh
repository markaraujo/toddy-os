#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','dconf'],text=True,env=env)=='install ok installed 0.49.0-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','dconf'],text=True,env=env).strip()=='0.49.0'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-dconf-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);native='/tmp/'+p.name;results={}
 for name,script,args in [('cli','dconf-probe.py',[]),('gsettings','dconf-gsettings-probe.py',['installed'])]:
  (p/script).write_bytes((Path('/opt/toddy-build/scripts/build/phase2')/script).read_bytes())
  r=subprocess.run(prefix+['python3','-B',native+'/'+script,'/',native+'/'+name,*args],env=env,capture_output=True,text=True,timeout=70,check=True);results[name]=json.loads(r.stdout)
assert results['cli']['isolated_user_database'] and results['gsettings']['mode']=='installed'
assert all(r['backend']=='DConfSettingsBackend' for r in results['gsettings']['cycles'])
Path('/var/log/toddy/phase2/dconf-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed native CLI/GSettings/private user DB persistence/refusal/reconnect/reset; no GNOME graphical acceptance','results':results},indent=2)+'\n')
PY
