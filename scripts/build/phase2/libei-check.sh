#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,shlex,subprocess,tempfile
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libei'],env=env,text=True)=='install ok installed 1.6.0-1+toddy1'
modules=['libei-1.0','libeis-1.0','liboeffis-1.0']
for pc in modules:assert subprocess.check_output(prefix+['pkg-config','--modversion',pc],env=env,text=True).strip()=='1.6.0'
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-libei-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);native='/tmp/'+p.name;(p/'consumer.c').write_bytes((root/'scripts/build/phase2/libei-probe.c').read_bytes())
 flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs',*modules],env=env,text=True))
 subprocess.run(prefix+['cc','-std=c11','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
 r=subprocess.run(prefix+[native+'/consumer'],env=env,text=True,capture_output=True,check=True)
Path('/var/log/toddy/phase2/libei-installed-consumer.json').write_text(json.dumps({'scope':'Native installed EI/EIS/Oeffis lifecycle/state/FD/refusal APIs only; no actual portal/physical input/GNOME acceptance','native_consumer_exit':0,'stdout':r.stdout},indent=2)+'\n')
PY
