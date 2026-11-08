#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,shlex,subprocess,tempfile
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs']
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root',
     'LIBGL_ALWAYS_SOFTWARE':'1','GALLIUM_DRIVER':'llvmpipe','EGL_PLATFORM':'surfaceless'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libepoxy'],text=True,env=env)=='install ok installed 1.5.10-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','epoxy'],text=True,env=env).strip()=='1.5.10'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-epoxy-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);(p/'consumer.c').write_bytes((root/'scripts/build/phase2/libepoxy-probe.c').read_bytes());native='/tmp/'+p.name
    env['XDG_CACHE_HOME']=native+'/cache'
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','epoxy'],text=True,env=env))
    subprocess.run(prefix+['cc','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    result=subprocess.run(prefix+[native+'/consumer'],text=True,capture_output=True,env=env,check=True)
    assert 'renderer: llvmpipe' in result.stdout
proof={'scope':'Native installed Epoxy dispatch over Mesa EGL/GLES shader/raster/pixel, no GNOME/window/physical/X11 acceptance',
       'native_consumer_exit':0,'version':'1.5.10','render_stdout':result.stdout,'stderr':result.stderr}
Path('/var/log/toddy/phase2/libepoxy-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
