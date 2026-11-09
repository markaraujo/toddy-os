#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'};prefix=['chroot','/mnt/lfs']
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libpsl'],text=True,env=env)=='install ok installed 0.23.3-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','libpsl'],text=True,env=env).strip()=='0.23.3'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip();subprocess.run(prefix+['apt-get','check'],env=env,check=True)
work=Path('/mnt/lfs/sources/phase2/work/libpsl-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-libpsl-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);shutil.copyfile(work/'native-probe',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((work/'native-probe').read_bytes()).digest() and not Path('/mnt/lfs/stage').exists()
 r=subprocess.run(prefix+['/tmp/'+p.name+'/probe'],env=env,capture_output=True,text=True,timeout=20,check=True);consumer=json.loads(r.stdout)
assert consumer==expected
Path('/var/log/toddy/phase2/libpsl-installed-consumer.json').write_text(json.dumps({'scope':'Installed builtin/runtime suffix/cookie refusal/Unicode/invalid converter/recovery/SDK/audit only; actual HTTP/browser/network pending','consumer':consumer,'IDNA_backend':'Owned ICU78.3, supported libicu option'},indent=2)+'\n')
PY
