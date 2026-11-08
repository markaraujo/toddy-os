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
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','mesa'],text=True,env=env)=='install ok installed 26.1.7-1+toddy1'
for name in ['egl','glesv2','gbm']:
    # These source Meson generators use project_version, not API/SONAME version.
    assert subprocess.check_output(prefix+['pkg-config','--modversion',name],text=True,env=env).strip()=='26.1.7'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-mesa-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);(p/'consumer.c').write_bytes((root/'scripts/build/phase2/mesa-probe.c').read_bytes());native='/tmp/'+p.name
    env['XDG_CACHE_HOME']=native+'/cache'
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','egl','glesv2'],text=True,env=env))
    subprocess.run(prefix+['cc','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    result=subprocess.run(prefix+[native+'/consumer'],text=True,capture_output=True,env=env,check=True)
    assert 'renderer: llvmpipe' in result.stdout
proof={'scope':'Native installed software EGL/GLES shaders/rasterization/pixel readback, not GNOME/window/physical GPU acceptance',
       'native_consumer_exit':0,'version':'26.1.7','render_stdout':result.stdout,
       'stderr':result.stderr,'runtime_versions':{'egl':'26.1.7','glesv2':'26.1.7','gbm':'26.1.7'}}
Path('/var/log/toddy/phase2/mesa-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
