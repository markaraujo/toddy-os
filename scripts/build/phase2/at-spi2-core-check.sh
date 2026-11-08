#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,shlex,subprocess,tempfile
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','at-spi2-core'],env=env,text=True)=='install ok installed 2.60.6-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','atspi-2'],env=env,text=True).strip()=='2.60.6'
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-at-spi2-core-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);native='/tmp/'+p.name;(p/'consumer.c').write_bytes((root/'scripts/build/phase2/at-spi2-core-probe.c').read_bytes())
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','atspi-2','atk'],env=env,text=True))
    subprocess.run(prefix+['cc','-std=c11','-D_GNU_SOURCE','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    r=subprocess.run(prefix+[native+'/consumer'],env=env,text=True,capture_output=True,check=True)
subprocess.run(prefix+['python3','-B','-c',"import gi;gi.require_version('Atk','1.0');gi.require_version('Atspi','2.0');from gi.repository import Atk,Atspi;a=Atk.StateSet.new();assert a.add_state(Atk.StateType.FOCUSED) and a.contains_state(Atk.StateType.FOCUSED);assert a.remove_state(Atk.StateType.FOCUSED);b=Atspi.StateSet.new([]);b.add(Atspi.StateType.FOCUSED);assert b.contains(Atspi.StateType.FOCUSED);b.remove(Atspi.StateType.FOCUSED);assert not b.contains(Atspi.StateType.FOCUSED)"],env=env,check=True)
Path('/var/log/toddy/phase2/at-spi2-core-installed-consumer.json').write_text(json.dumps({'scope':'Native installed ATK/AT-SPI state APIs, not a graphical session',
    'native_consumer_exit':0,'stdout':r.stdout,'stderr':r.stderr,'gi_exit':0},indent=2)+'\n')
PY
