#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'CHECK'
from pathlib import Path
import json,subprocess,tempfile
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','cbindgen'],text=True,env=env)=='install ok installed 0.29.4-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-cbindgen-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);(p/'probe.py').write_bytes((root/'scripts/build/phase2/cbindgen_probe.py').read_bytes());native='/tmp/'+p.name
    subprocess.run(prefix+['python3',native+'/probe.py','/usr/bin/cbindgen',native+'/abi-consumer'],env=env,check=True)
    result=json.loads((p/'abi-consumer/result.json').read_text())
proof={'scope':'Actual installed cbindgen C/C++ generated headers/native Rust ABI and malformed-input refusal; macro/Cython/desktop unqualified','version':'0.29.4','native_consumer_exit':0,'consumer':result}
Path('/var/log/toddy/phase2/cbindgen-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
CHECK
