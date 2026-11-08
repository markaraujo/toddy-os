#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess,tempfile
prefix=['chroot','/mnt/lfs']
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','rustc'],env=env,text=True)=='install ok installed 1.97.1-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
for name in ['rustc','cargo','rustdoc','rustfmt','clippy-driver','cargo-clippy']:
    assert subprocess.check_output(prefix+['dpkg-query','-S','/usr/bin/'+name],env=env,text=True).startswith('rustc: ')
body=Path('/opt/toddy-build/scripts/build/phase2/rust_tools_probe.py').read_text()
with tempfile.TemporaryDirectory(prefix='toddy-rust-installed-',dir='/mnt/lfs/tmp') as temporary:
    work='/tmp/'+Path(temporary).name+'/probe'
    subprocess.run(prefix+['/usr/bin/python3','-c',body,'/usr',work],env=env,check=True)
    result=json.loads((Path(temporary)/'probe/results.json').read_text())
    Path('/var/log/toddy/phase2/rustc-installed-tools.json').write_text(json.dumps(result,indent=2)+'\n')
PY
