#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','fmt'],text=True)=='install ok installed 12.2.0-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','fmt'],text=True).strip()=='12.2.0'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
expected=json.loads((T/'sources/phase2/work/fmt-1/stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-fmt-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755)
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/fmt-probe.py',p/'probe.py')
 virtual='/tmp/'+p.name;env.update(HOME=virtual)
 actual=json.loads(subprocess.check_output(['unshare','--net','chroot','--userspec=101:101',str(T),'python3',virtual+'/probe.py','/usr',virtual],env=env,text=True,timeout=40));assert actual==expected
 libs=subprocess.check_output(prefix+['ldd',virtual+'/consumer/compile/consumer'],env=env,text=True);assert 'libfmt.so.12 => /usr/lib/libfmt.so.12' in libs
Path('/var/log/toddy/phase2/fmt-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed UID101 exact CMake/shared fmt12.2 discovery/Unicode decimal+hex/runtime-format-error refusal/two recovery cycles in private no-route namespace, actual libfmt.so.12 resolution/pkg-config/APT0. No VTE/terminal/GUI acceptance; bundled original GTest is not shipped by this package.','consumer':actual,'shared_libfmt_resolution':True,'pkg_config_version':'12.2.0'},indent=2)+'\n')
PY
