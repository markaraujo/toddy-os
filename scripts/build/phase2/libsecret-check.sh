#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libsecret'],text=True,env=env)=='install ok installed 0.21.7-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','libsecret-1'],text=True,env=env).strip()=='0.21.7'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
work=Path('/mnt/lfs/sources/phase2/work/libsecret-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-libsecret-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);shutil.copyfile(work/'native-probe',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((work/'native-probe').read_bytes()).digest() and not Path('/mnt/lfs/stage').exists()
 r=subprocess.run(prefix+['/tmp/'+p.name+'/probe'],env=env,capture_output=True,text=True,timeout=20,check=True);consumer=json.loads(r.stdout)
assert consumer==expected
code="import gi,json\ngi.require_version('Secret','1')\nfrom gi.repository import Secret\nassert Secret.Value.__gtype__.name=='SecretValue' and Secret.Service.__gtype__.name=='SecretService'\nprint(json.dumps({'native_gi_types':['SecretValue','SecretService']}))"
r=subprocess.run(prefix+['python3','-B','-c',code],env=env,capture_output=True,text=True,timeout=20,check=True)
Path('/var/log/toddy/phase2/libsecret-installed-consumer.json').write_text(json.dumps({'scope':'Installed binary/schema/refusal/lifecycle/GI/SDK/package audit only; actual keyring/provider/real credentials/graphical acceptance pending','consumer':consumer,'gi':json.loads(r.stdout),'optional_PAM_and_TPM':'Not built or enabled'},indent=2)+'\n')
PY
