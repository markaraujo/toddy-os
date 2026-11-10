#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libndp'],text=True)=='install ok installed 1.9-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','libndp'],text=True).strip()=='1.9'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
w=Path('/mnt/lfs/sources/phase2/work/libndp-1');expected=json.loads((w/'stage-results.json').read_text())['consumer'];assert not Path('/mnt/lfs/stage').exists()
with tempfile.TemporaryDirectory(prefix='toddy-libndp-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);p.chmod(0o755);shutil.copyfile(w/'native-probe',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((w/'native-probe').read_bytes()).digest()
 native='/tmp/'+p.name+'/probe';libs=subprocess.check_output(prefix+['ldd',native],text=True,env=env);assert 'libndp.so.0 => /usr/lib/libndp.so.0' in libs
 actual=json.loads(subprocess.check_output(['chroot','--userspec=101:101','/mnt/lfs',native],env=env,text=True,timeout=20));assert actual==expected
helptext=subprocess.check_output(prefix+['ndptool','--help'],text=True,env=env,stderr=subprocess.STDOUT);assert '--help' in helptext
Path('/var/log/toddy/phase2/libndp-installed-consumer.json').write_text(json.dumps({'scope':'Owned library/SDK and real UID101 typed five-message creation/wildcard refusal/payload clamp/two-cycle recovery; CLI help only. No NDP traffic, device, raw-socket privilege or actual NetworkManager acceptance.','consumer':actual,'loaded_owned_library':True,'CLI_help':True},indent=2)+'\n')
PY
