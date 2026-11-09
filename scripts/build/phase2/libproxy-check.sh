#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libproxy'],text=True)=='install ok installed 0.5.12-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','libproxy-1.0'],text=True).strip()=='0.5.12'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
work=Path('/mnt/lfs/sources/phase2/work/libproxy-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
assert not Path('/mnt/lfs/stage').exists()
with tempfile.TemporaryDirectory(prefix='toddy-libproxy-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);shutil.copyfile(work/'native-probe',p/'probe');(p/'probe').chmod(0o755)
    assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((work/'native-probe').read_bytes()).digest()
    native='/tmp/'+p.name+'/probe';libs=subprocess.check_output(prefix+['ldd',native],text=True,env=env)
    assert 'libproxy.so.1 => /usr/lib/libproxy.so.1' in libs and 'libpxbackend-1.0.so => /usr/lib/libproxy/libpxbackend-1.0.so' in libs
    consumer=json.loads(subprocess.check_output(prefix+[native],env=env,text=True,timeout=20));assert consumer==expected
Path('/var/log/toddy/phase2/libproxy-installed-consumer.json').write_text(json.dumps({'scope':'Owned public direct/bypass/malformed-URI safe fallback/boxed lifetime and SDK only; original loopback PAC/Duktape fixtures reused. Remote proxy/PAC/WPAD/portal and native GNOME integration pending.','consumer':consumer,'loaded_owned_frontend_and_backend':True,'SDK_version':'0.5.12'},indent=2)+'\n')
PY
