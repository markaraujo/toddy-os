#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs']
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','pyyaml'],text=True,env=env)=='install ok installed 6.0.3-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
body=(root/'scripts/build/phase2/pyyaml-probe.py').read_text()
proof=json.loads(subprocess.check_output(prefix+['python3','-B','-c',body],env=env,text=True))
assert proof['uid']==0
Path('/var/log/toddy/phase2/pyyaml-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
