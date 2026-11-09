#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','upower'],text=True,env=env)=='install ok installed 1.91.3-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','upower-glib'],text=True,env=env).strip()=='1.91.3'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-upower-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);script=p/'probe.py';script.write_bytes(Path('/opt/toddy-build/scripts/build/phase2/upower-probe.py').read_bytes())
 r=subprocess.run(prefix+['python3','-B','/tmp/'+p.name+'/probe.py','/'],env=env,capture_output=True,text=True,timeout=20,check=True);consumer=json.loads(r.stdout)
assert consumer['cli_help_exit']==0 and consumer['typed_history_roundtrip']
Path('/var/log/toddy/phase2/upower-installed-consumer.json').write_text(json.dumps({'scope':'Installed CLI-help/GI/SDK/package audit; real native service separately qualified. Shared systemd hwdb cache update required before desktop/device acceptance; no physical battery claim','consumer':consumer,'shared_hwdb_update':'pending controlled same-version cache integration'},indent=2)+'\n')
PY
