#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,shlex,subprocess,tempfile
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','lcms2'],env=env,text=True)=='install ok installed 2.19.1-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','lcms2'],env=env,text=True).strip()=='2.19'
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-lcms2-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);native='/tmp/'+p.name;(p/'consumer.c').write_bytes((root/'scripts/build/phase2/lcms2-probe.c').read_bytes())
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','lcms2'],env=env,text=True))
    subprocess.run(prefix+['cc','-std=c11','-D_GNU_SOURCE','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    r=subprocess.run(prefix+[native+'/consumer'],env=env,text=True,capture_output=True,check=True)
Path('/var/log/toddy/phase2/lcms2-installed-consumer.json').write_text(json.dumps({'scope':'Native installed ICC serialization/reopen/navy identity and malformed-profile refusal; not physical color calibration',
    'native_consumer_exit':0,'stdout':r.stdout,'stderr':r.stderr,'icc_roundtrip':True,'malformed_icc_refusal':True},indent=2)+'\n')
PY
