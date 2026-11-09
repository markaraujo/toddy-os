#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,shlex,subprocess,tempfile
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','mtdev'],env=env,text=True)=='install ok installed 1.1.7-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','mtdev'],env=env,text=True).strip()=='1.1.7'
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-mtdev-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);native='/tmp/'+p.name;(p/'consumer.c').write_bytes((root/'scripts/build/phase2/mtdev-probe.c').read_bytes())
 flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','mtdev'],env=env,text=True))
 subprocess.run(prefix+['cc','-std=c11','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
 r=subprocess.run(prefix+[native+'/consumer'],env=env,text=True,capture_output=True,check=True)
Path('/var/log/toddy/phase2/mtdev-installed-consumer.json').write_text(json.dumps({'scope':'Native installed capabilities/event-frame/cleanup/refusal only; physical device and GNOME input pending','native_consumer_exit':0,'stdout':r.stdout},indent=2)+'\n')
PY
