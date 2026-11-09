#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gcr'],text=True,env=env)=='install ok installed 4.4.0.1-1+toddy1'
for name,version in [('gcr-4','4.4.0.1'),('gck-2','4.4.0.1')]:assert subprocess.check_output(prefix+['pkg-config','--modversion',name],text=True,env=env).strip()==version
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
work=Path('/mnt/lfs/sources/phase2/work/gcr-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-gcr-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);shutil.copyfile(work/'native-probe',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((work/'native-probe').read_bytes()).digest() and not Path('/mnt/lfs/stage').exists()
 r=subprocess.run(prefix+['/tmp/'+p.name+'/probe'],env=env,capture_output=True,text=True,timeout=20,check=True);consumer=json.loads(r.stdout)
assert consumer==expected
code="import gi,json\ngi.require_version('Gcr','4');gi.require_version('Gck','2')\nfrom gi.repository import Gcr,Gck\nassert Gcr.SecretExchange.__gtype__.name=='GcrSecretExchange' and Gck.Module.__gtype__.name=='GckModule'\nprint(json.dumps({'native_gi_types':['GcrSecretExchange','GckModule']}))"
r=subprocess.run(prefix+['python3','-B','-c',code],env=env,capture_output=True,text=True,timeout=20,check=True)
assert not Path('/mnt/lfs/usr/libexec/gcr-ssh-agent').exists()
Path('/var/log/toddy/phase2/gcr-installed-consumer.json').write_text(json.dumps({'scope':'Installed transport/GI/SDK/package audit, no graphical prompt/keyring/real-credential acceptance. Optional SSH-agent not built/enabled','consumer':consumer,'gi':json.loads(r.stdout)},indent=2)+'\n')
PY
