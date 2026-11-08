#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
import json,subprocess,tempfile
from pathlib import Path
root=Path('/opt/toddy-build')
config=(root/'config/phase2/python-test-tools.lock.json').read_bytes()
rows=json.loads(config)['packages'];prefix=['chroot','/mnt/lfs']
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root',
     'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'}
for row in rows:
    status=subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}',row['name']],env=env,text=True)
    assert status=='install ok installed '+row['version']+'-1+toddy1',status
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
body=(root/'scripts/build/phase2/python_tools_probe.py').read_text()
with tempfile.TemporaryDirectory(prefix='toddy-python-tools-',dir='/mnt/lfs/tmp') as directory:
    temporary=Path(directory);(temporary/'config.json').write_bytes(config)
    native='/tmp/'+temporary.name
    output=subprocess.check_output(prefix+['/usr/bin/python3','-B','-c',body,native+'/config.json',native+'/consumer'],env=env,text=True)
    proof=json.loads(output)
    Path('/var/log/toddy/phase2/python-test-tools-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
