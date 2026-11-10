#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','simdutf'],text=True)=='install ok installed 9.0.0-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','simdutf'],text=True).strip()=='9.0.0'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
expected=json.loads((T/'sources/phase2/work/simdutf-1/stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-simdutf-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755)
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/simdutf-probe.py',p/'probe.py')
 virtual='/tmp/'+p.name;env.update(HOME=virtual)
 actual=json.loads(subprocess.check_output(['unshare','--net','chroot','--userspec=101:101',str(T),'python3',virtual+'/probe.py','/usr',virtual],env=env,text=True,timeout=40));assert actual==expected
 libs=subprocess.check_output(prefix+['ldd',virtual+'/consumer/compile/consumer'],env=env,text=True);assert 'libsimdutf.so.34 => /usr/lib/libsimdutf.so.34' in libs
Path('/var/log/toddy/phase2/simdutf-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed UID101 CMake/shared simdutf34 exact discovery/Portuguese-emoji UTF8↔UTF16 roundtrip/typed lengths/overlong+surrogate refusal/two recovery cycles in private no-route namespace, actual shared ABI/pkg-config/APT0. Original91programs/79unsupported icelake notes retained; no other-CPU/terminal/GUI acceptance. Optional CLI tools not installed.','consumer':actual,'shared_libsimdutf_resolution':True,'pkg_config_version':'9.0.0','unsupported_CPU_branch':'icelake','unsupported_CPU_notes':79},indent=2)+'\n')
PY
