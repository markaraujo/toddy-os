#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'CHECK'
from pathlib import Path
import json,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','dbus-python'],text=True,env=env)=='install ok installed 1.4.0-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','dbus-python'],text=True,env=env).strip()=='1.4.0'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-dbus-python-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);native='/tmp/'+p.name;(p/'consumer.py').write_bytes(Path('/opt/toddy-build/scripts/build/phase2/dbus-python-probe.py').read_bytes())
 r=subprocess.run(prefix+['dbus-run-session','--','python3','-B',native+'/consumer.py'],env=env,capture_output=True,text=True,check=True);consumer=json.loads(r.stdout)
assert consumer['version']=='1.4.0' and consumer['distinct_connections'] and all(x['uid']==0 and x['missing_peer_refused'] and x['recovery_call'] for x in consumer['cycles'])
proof={'scope':'Actual installed native Python module/private dbus-daemon typed UID/error/name/reconnect; test-only dependency. Original repeated embedded interpreter initialization remains unsupported on Python>=3.12; not a passed case. No Polkit/GNOME acceptance.','version':'1.4.0','consumer':consumer}
Path('/var/log/toddy/phase2/dbus-python-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
CHECK
