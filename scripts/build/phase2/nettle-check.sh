#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'};prefix=['chroot','/mnt/lfs']
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','nettle'],text=True,env=env)=='install ok installed 4.0-1+toddy1'
for pc in ['nettle','hogweed']:assert subprocess.check_output(prefix+['pkg-config','--modversion',pc],text=True,env=env).strip()=='4.0'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip();subprocess.run(prefix+['apt-get','check'],env=env,check=True)
work=Path('/mnt/lfs/sources/phase2/work/nettle-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-nettle-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);shutil.copyfile(work/'native-probe-2',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((work/'native-probe-2').read_bytes()).digest() and not Path('/mnt/lfs/stage').exists()
 r=subprocess.run(prefix+['/tmp/'+p.name+'/probe'],env=env,capture_output=True,text=True,timeout=20,check=True);consumer=json.loads(r.stdout)
assert consumer==expected
Path('/var/log/toddy/phase2/nettle-installed-consumer.json').write_text(json.dumps({'scope':'Installed actual SHA256/Hogweed P256/zero-scalar/off-curve refusal/recovery/SDK/audit only; original x86-ibt unavailable, TLS/GnuTLS/network/native GNOME pending','consumer':consumer},indent=2)+'\n')
PY
