#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
import json,subprocess,tempfile
from pathlib import Path
prefix=['chroot','/mnt/lfs']
env={'PATH':'/usr/bin:/usr/sbin','HOME':'/root','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','mako'],env=env,text=True)=='install ok installed 1.4.1-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
assert subprocess.check_output(prefix+['dpkg-query','-S','/usr/lib/python3.14/site-packages/mako/__init__.py'],env=env,text=True).startswith('mako: ')
body=Path('/opt/toddy-build/scripts/build/phase2/mako-probe.py').read_text()
with tempfile.TemporaryDirectory(prefix='toddy-mako-',dir='/mnt/lfs/tmp') as directory:
    work='/tmp/'+Path(directory).name+'/consumer'
    output=subprocess.check_output(prefix+['/usr/bin/python3','-B','-c',body,work],env=env,text=True)
    proof=json.loads(output);assert len(proof['checks'])==6 and proof['c_consumer_exit']==0
    Path('/var/log/toddy/phase2/mako-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
