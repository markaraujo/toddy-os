#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'};prefix=['chroot','/mnt/lfs']
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','libunistring'],text=True,env=env)=='install ok installed 1.4.2-1+toddy1'
assert '#define _LIBUNISTRING_VERSION 0x010402' in Path('/mnt/lfs/usr/include/unistring/version.h').read_text()
code="import ctypes;lib=ctypes.CDLL('/usr/lib/libunistring.so');assert ctypes.c_int.in_dll(lib,'_libunistring_version').value==0x010402"
subprocess.run(prefix+['python3','-c',code],env=env,capture_output=True,text=True,timeout=15,check=True)
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip();subprocess.run(prefix+['apt-get','check'],env=env,check=True)
work=Path('/mnt/lfs/sources/phase2/work/libunistring-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-libunistring-',dir='/mnt/lfs/tmp') as directory:
 p=Path(directory);shutil.copyfile(work/'native-probe-2',p/'probe');(p/'probe').chmod(0o755)
 assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((work/'native-probe-2').read_bytes()).digest() and not Path('/mnt/lfs/stage').exists()
 r=subprocess.run(prefix+['/tmp/'+p.name+'/probe'],env=env,capture_output=True,text=True,timeout=20,check=True);consumer=json.loads(r.stdout)
assert consumer==expected
Path('/var/log/toddy/phase2/libunistring-installed-consumer.json').write_text(json.dumps({'scope':'Installed UTF8 validation/NFC/Portuguese case/invalid UTF8/prior state/lifecycle/SDK/dynamic version/audit only; GnuTLS/TLS/native GNOME pending','consumer':consumer,'version':'1.4.2','malformed_input_handling':'Reject via u8_check before normalization; no claim that u8_normalize validates malformed UTF8'},indent=2)+'\n')
PY
