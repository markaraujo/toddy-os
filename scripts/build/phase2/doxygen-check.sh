#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess,tempfile
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','doxygen'],env=env,text=True)=='install ok installed 1.18.0-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
body=(root/'scripts/build/phase2/doxygen-probe.py').read_text()
with tempfile.TemporaryDirectory(prefix='toddy-doxygen-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);native='/tmp/'+p.name
    r=subprocess.run(prefix+['python3','-B','-c',body,native+'/consumer'],env=env,text=True,capture_output=True,check=True)
    proof=json.loads((p/'consumer/results.json').read_text());assert proof['generator_exit']==proof['schema_exit']==0
Path('/var/log/toddy/phase2/doxygen-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
