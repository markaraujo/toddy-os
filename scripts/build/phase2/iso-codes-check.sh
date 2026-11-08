#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','iso-codes'],env=env,text=True)=='install ok installed 4.20.1-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','iso-codes'],env=env,text=True).strip()=='4.20.1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
body=Path('/opt/toddy-build/scripts/build/phase2/iso-codes-probe.py').read_text()
r=subprocess.run(prefix+['python3','-B','-c',body],env=env,text=True,capture_output=True,check=True)
Path('/var/log/toddy/phase2/iso-codes-installed-consumer.json').write_text(json.dumps({'native_consumer_exit':0,'consumer':json.loads(r.stdout)},indent=2)+'\n')
PY
