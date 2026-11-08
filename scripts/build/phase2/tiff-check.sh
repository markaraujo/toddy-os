#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,shlex,subprocess,tempfile
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','tiff'],env=env,text=True)=='install ok installed 4.7.2-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','libtiff-4'],env=env,text=True).strip()=='4.7.2'
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-tiff-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);native='/tmp/'+p.name;(p/'consumer.c').write_bytes((root/'scripts/build/phase2/tiff-probe.c').read_bytes())
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','libtiff-4'],env=env,text=True))
    subprocess.run(prefix+['cc','-std=c11','-D_GNU_SOURCE','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    r=subprocess.run(prefix+[native+'/consumer'],env=env,text=True,capture_output=True,check=True)
Path('/var/log/toddy/phase2/tiff-installed-consumer.json').write_text(json.dumps({'scope':'Native installed bounded TIFF image APIs, not Gdk TIFF loader or a graphical session',
    'native_consumer_exit':0,'stdout':r.stdout,'stderr':r.stderr,'allocation_limit_bytes':16*1024**2},indent=2)+'\n')
PY
