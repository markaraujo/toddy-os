#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'CHECK'
from pathlib import Path
import json,shlex,subprocess,tempfile
name='libsndfile';version='1.2.2';pc='sndfile'
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
status=subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}',name],text=True,env=env)
assert status=='install ok installed '+version+'-1+toddy1',status
assert subprocess.check_output(prefix+['pkg-config','--modversion',pc],text=True,env=env).strip()==version
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-'+name+'-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);(p/'consumer.c').write_bytes((root/'scripts/build/phase2'/(name+'-probe.c')).read_bytes());native='/tmp/'+p.name
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs',pc],text=True,env=env))
    subprocess.run(prefix+['cc','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    result=subprocess.run(prefix+[native+'/consumer'],env=env,check=True,capture_output=True,text=True)
proof={'scope':'Native installed exact PCM WAV write/reopen/samples/absent-file refusal; no audible output acceptance','name':name,'version':version,'native_consumer_exit':0,'stdout':result.stdout.strip()}
Path('/var/log/toddy/phase2',name+'-installed-consumer.json').write_text(json.dumps(proof,indent=2)+chr(10))
CHECK
