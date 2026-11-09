#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','python-dbusmock'],text=True,env=env)=='install ok installed 0.38.1-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-dbusmock-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);native='/tmp/'+p.name;(p/'consumer.py').write_bytes(Path('/opt/toddy-build/scripts/build/phase2/python-dbusmock-probe.py').read_bytes())
 r=subprocess.run(prefix+['python3','-B',native+'/consumer.py'],env=env,capture_output=True,text=True,check=True);consumer=json.loads(r.stdout)
assert consumer['version']=='0.38.1' and len(consumer['cycles'])==2
assert all(r['unknown_method_refused'] and r['recovery'] for r in consumer['cycles'])
Path('/var/log/toddy/phase2/python-dbusmock-installed-consumer.json').write_text(json.dumps(consumer,indent=2)+'\n')
PY
