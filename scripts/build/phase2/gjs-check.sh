#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'CHECK'
from pathlib import Path
import json,shlex,subprocess,tempfile
root=Path('/opt/toddy-build/scripts/build/phase2');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
status=subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gjs'],text=True,env=env)
assert status=='install ok installed 1.88.1-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','gjs-1.0'],text=True,env=env).strip()=='1.88.1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-gjs-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);native='/tmp/'+p.name
    (p/'consumer.c').write_bytes((root/'gjs-probe.c').read_bytes())
    (p/'probe.py').write_bytes((root/'gjs_probe.py').read_bytes())
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','gjs-1.0'],text=True,env=env))
    subprocess.run(prefix+['cc','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    result=subprocess.run(prefix+[native+'/consumer'],env=env,text=True,capture_output=True,check=True)
    code="import importlib.util,json,os;from pathlib import Path;spec=importlib.util.spec_from_file_location('toddy_native_gjs',"+repr(native+'/probe.py')+");module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);print(json.dumps(module.run('/usr/bin/gjs',Path("+repr(native+'/cli')+"),dict(os.environ))))"
    cli=subprocess.run(prefix+['python3','-B','-c',code],env=env,text=True,capture_output=True,check=True)
proof={'scope':'Actual installed GJS public C embedding/GI/refusal/recovery and CLI ES module/native GLib event/Gio refusal; native original78drivers passed separately,147upstream pending cases remain skips; no full GNOME session claim','version':'1.88.1','native_c_consumer_exit':0,'stdout':result.stdout.strip(),'cli':json.loads(cli.stdout)}
Path('/var/log/toddy/phase2/gjs-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
CHECK
