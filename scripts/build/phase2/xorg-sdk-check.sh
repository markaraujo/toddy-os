#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
import json, subprocess, tempfile
from pathlib import Path
root=Path('/opt/toddy-build')
config=json.loads((root/'config/phase2/xorg-validation-sdk.lock.json').read_text())
prefix=['chroot','/mnt/lfs']
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root',
     'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'}
for row in config['packages']:
    status=subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}',row['name']],env=env,text=True)
    assert status=='install ok installed '+row['version']+'-1+toddy1',status
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
body=(root/'scripts/build/phase2/xorg_sdk_probe.py').read_text()
with tempfile.TemporaryDirectory(prefix='toddy-xorg-sdk-',dir='/mnt/lfs/tmp') as directory:
    native='/tmp/'+Path(directory).name
    subprocess.run(prefix+['python3','-B','-c',body,'/usr',native+'/consumer'],env=env,check=True)
    proof=json.loads((Path(directory)/'consumer/results.json').read_text())
    assert proof['uid']==0
    assert Path('/mnt/lfs/usr/share/X11/locale/en_US.UTF-8/Compose').is_file()
    proof['installed_compose_data']=True
    Path('/var/log/toddy/phase2/xorg-validation-sdk-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
