#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess,tempfile
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs']
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','CARGO_NET_OFFLINE':'true','CARGO_BUILD_JOBS':'4'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','cargo-c'],text=True,env=env)=='install ok installed 0.10.24-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
body=(root/'scripts/build/phase2/cargo_c_probe.py').read_text()
with tempfile.TemporaryDirectory(prefix='toddy-cargo-c-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);native='/tmp/'+p.name;(p/'home').mkdir()
    (p/'home/config.toml').write_text('[net]\noffline=true\n')
    env['CARGO_HOME']=native+'/home';env['HOME']=native+'/home'
    subprocess.run(prefix+['python3','-B','-c',body,native+'/consumer'],env=env,check=True)
    proof=json.loads((p/'consumer/results.json').read_text());assert proof['uid']==0
    Path('/var/log/toddy/phase2/cargo-c-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
