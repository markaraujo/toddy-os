#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'CHECK'
from pathlib import Path
import json,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','duktape'],text=True,env=env)=='install ok installed 2.7.0-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','duktape'],text=True,env=env).strip()=='2.7.0'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
records=[]
with tempfile.TemporaryDirectory(prefix='toddy-duktape-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);native='/tmp/'+p.name
 (p/'consumer.c').write_bytes(Path('/opt/toddy-build/scripts/build/phase2/duktape-probe.c').read_bytes())
 for name in ['duktape','duktaped']:
  subprocess.run(prefix+['cc','-Wall','-Wextra','-Werror',native+'/consumer.c','-l'+name,'-o',native+'/'+name],env=env,check=True)
  r=subprocess.run(prefix+[native+'/'+name],env=env,capture_output=True,text=True,check=True);proof=json.loads(r.stdout)
  assert proof=={'version':20700,'checks':15,'bytecode_load_dump':'unsupported','recovery':True};records.append({'library':name,'exit':0,**proof})
proof={'scope':'Actual installed normal/debug C policy-engine profile15checks each; no Polkit daemon/authorization/GNOME acceptance','version':'2.7.0','records':records}
Path('/var/log/toddy/phase2/duktape-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
CHECK
