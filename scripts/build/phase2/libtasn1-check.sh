#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libtasn1'],text=True,env=env)=='install ok installed 4.21.0-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','libtasn1'],text=True,env=env).strip()=='4.21.0'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
work=Path('/mnt/lfs/sources/phase2/work/libtasn1-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-libtasn1-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);shutil.copyfile(work/'native-probe',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((work/'native-probe').read_bytes()).digest()
 # Build-only /stage RUNPATH is absent here; loader resolves actual installed /usr.
 assert not Path('/mnt/lfs/stage').exists()
 r=subprocess.run(prefix+['/tmp/'+p.name+'/probe'],env=env,capture_output=True,text=True,timeout=15,check=True);consumer=json.loads(r.stdout)
assert consumer==expected
Path('/var/log/toddy/phase2/libtasn1-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed ASN.1 strict DER/refusal/recovery/SDK/package audit only; PKCS11/trust/GNOME integration pending','consumer':consumer},indent=2)+'\n')
PY
