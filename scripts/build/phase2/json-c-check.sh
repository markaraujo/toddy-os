#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','json-c'],text=True,env=env)=='install ok installed 0.19-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','json-c'],text=True,env=env).strip()=='0.19'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
assert not Path('/mnt/lfs/usr/bin/json_parse').exists()
with tempfile.TemporaryDirectory(prefix='toddy-json-c-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);native='/tmp/'+p.name;(p/'consumer.c').write_bytes(Path('/opt/toddy-build/scripts/build/phase2/json-c-probe.c').read_bytes())
 subprocess.run(prefix+['bash','-c','cc -Wall -Wextra -Werror "$1/consumer.c" $(pkg-config --cflags --libs json-c) -o "$1/consumer"','probe',native],check=True,env=env)
 r=subprocess.run(prefix+[native+'/consumer'],env=env,capture_output=True,text=True,check=True);consumer=json.loads(r.stdout)
assert consumer['version']=='0.19' and all(consumer[k] for k in ['typed_identity','unicode','false_permission_preserved','malformed_refused','invalid_utf8_refused','depth_bound_refused','recovery'])
Path('/var/log/toddy/phase2/json-c-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed strict native C parser/UTF8/depth/refusal/recovery and APT audit; no AccountsService/GNOME acceptance','consumer':consumer},indent=2)+'\n')
PY
