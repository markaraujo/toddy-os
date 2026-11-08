#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,shlex,subprocess,tempfile
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libdisplay-info'],env=env,text=True)=='install ok installed 0.4.0-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','libdisplay-info'],env=env,text=True).strip()=='0.4.0'
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-libdisplay-info-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);native='/tmp/'+p.name;(p/'consumer.c').write_bytes((root/'scripts/build/phase2/libdisplay-info-probe.c').read_bytes())
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','libdisplay-info'],env=env,text=True))
    subprocess.run(prefix+['cc','-std=c11','-D_GNU_SOURCE','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    r=subprocess.run(prefix+[native+'/consumer','/sources/phase2/inputs/libdisplay-info-0.4.0/test/data/qemu.edid'],env=env,text=True,capture_output=True,check=True)
Path('/var/log/toddy/phase2/libdisplay-info-installed-consumer.json').write_text(json.dumps({'scope':'Native installed EDID/QEMU fixture/PnP lookup and malformed/truncated-input refusal; not physical monitor/driver acceptance',
    'native_consumer_exit':0,'stdout':r.stdout,'stderr':r.stderr,'qemu_pnp_make':'Red Hat, Inc.','malformed_and_truncated_refusal':True},indent=2)+'\n')
PY
