#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libsoup'],text=True)=='install ok installed 3.6.6-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','libsoup-3.0'],text=True).strip()=='3.6.6'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
work=Path('/mnt/lfs/sources/phase2/work/libsoup-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-libsoup-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);shutil.copyfile(work/'native-probe',p/'probe');(p/'probe').chmod(0o755)
    assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((work/'native-probe').read_bytes()).digest()
    native='/tmp/'+p.name+'/probe';libs=subprocess.check_output(prefix+['ldd',native],env=env,text=True)
    assert 'libsoup-3.0.so.0 => /usr/lib/libsoup-3.0.so.0' in libs and '/stage/' not in libs
    consumer=json.loads(subprocess.check_output(prefix+[native],env=env,text=True,timeout=60));assert consumer==expected
Path('/var/log/toddy/phase2/libsoup-installed-consumer.json').write_text(json.dumps({'scope':'Owned installed actual private-loopback HTTP client/server, pre-cancelled request/refusal/no dispatch/recovery and SDK. Original35driver passes with22nested skips reused; remote network/Apache/NTLM helper/native GNOME/browser pending.','consumer':consumer,'loaded_owned_library':True,'SDK_version':'3.6.6'},indent=2)+'\n')
PY
