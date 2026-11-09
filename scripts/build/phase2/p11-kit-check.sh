#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','p11-kit'],text=True,env=env)=='install ok installed 0.26.5-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','p11-kit-1'],text=True,env=env).strip()=='0.26.5'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
work=Path('/mnt/lfs/sources/phase2/work/p11-kit-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-p11-kit-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);shutil.copyfile(work/'native-probe',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((work/'native-probe').read_bytes()).digest() and not Path('/mnt/lfs/stage').exists()
 r=subprocess.run(prefix+['/tmp/'+p.name+'/probe'],env=env,capture_output=True,text=True,timeout=15,check=True);consumer=json.loads(r.stdout)
assert consumer==expected
assert Path('/mnt/lfs/usr/lib/pkcs11/p11-kit-trust.so').is_file()
assert not list(Path('/mnt/lfs/etc/systemd').glob('**/*.wants/p11-kit-server.*'))
Path('/var/log/toddy/phase2/p11-kit-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed URI/refusal/recovery/SDK/package audit only; no real credentials/token/root-store acceptance','consumer':consumer,'server_not_enabled_by_slice':True,'root_store_make_ca_and_NSS_alias':'Pending separate qualified integration'},indent=2)+'\n')
PY
