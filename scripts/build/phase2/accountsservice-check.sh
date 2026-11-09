#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','accountsservice'],text=True,env=env)=='install ok installed 26.27.3-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','accountsservice'],text=True,env=env).strip()=='26.27.3'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-accountsservice-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);script=p/'probe.py';script.write_bytes(Path('/opt/toddy-build/scripts/build/phase2/accountsservice-probe.py').read_bytes())
 r=subprocess.run(prefix+['python3','-B','/tmp/'+p.name+'/probe.py','/'],env=env,capture_output=True,text=True,timeout=20,check=True);consumer=json.loads(r.stdout)
assert consumer['daemon_version_exit']==0 and consumer['native_gi_types']==['ActUser','ActUserManager']
assert Path('/mnt/lfs/usr/lib/systemd/system/accounts-daemon.service').is_file()
Path('/var/log/toddy/phase2/accountsservice-installed-consumer.json').write_text(json.dumps({'scope':'Installed CLI/GI/SDK/package audit; real native account gate separately source-bound, GNOME UI pending','consumer':consumer},indent=2)+'\n')
PY
