#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
import json,shlex,subprocess,tempfile
from pathlib import Path
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs']
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
for name,version in [('xkeyboard-config','2.48'),('libxkbcommon','1.13.2')]:
    status=subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}',name],text=True,env=env)
    assert status=='install ok installed '+version+'-1+toddy1',status
for name,version in [('xkeyboard-config','2.48'),('xkbcommon','1.13.2'),('xkbregistry','1.13.2')]:
    assert subprocess.check_output(prefix+['pkg-config','--modversion',name],text=True,env=env).strip()==version
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-keyboard-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);(p/'consumer.c').write_bytes((root/'scripts/build/phase2/keyboard-probe.c').read_bytes())
    native='/tmp/'+p.name
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','xkbcommon','xkbregistry'],text=True,env=env))
    subprocess.run(prefix+['cc',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    subprocess.run(prefix+[native+'/consumer','/usr/share/xkeyboard-config-2'],env=env,check=True)
result={'scope':'Native installed US/BR/PT keymaps, Shift a/A/a, registry and frozen default include root; no physical/GUI proof','consumer_exit':0,
        'versions':{'xkeyboard-config':'2.48','xkbcommon':'1.13.2','xkbregistry':'1.13.2'},'wayland':True,'x11_library':False}
Path('/var/log/toddy/phase2/keyboard-installed-consumer.json').write_text(json.dumps(result,indent=2)+'\n')
PY
