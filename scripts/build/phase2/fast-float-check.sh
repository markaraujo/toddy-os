#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version} ${Architecture}','fast-float'],text=True)=='install ok installed 8.2.10-1+toddy1 all'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
expected=json.loads((T/'sources/phase2/work/fast-float-1/stage-results.json').read_text())['consumer']
with tempfile.TemporaryDirectory(prefix='toddy-fast-float-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755)
 shutil.copyfile('/opt/toddy-build/scripts/build/phase2/fast-float-probe.py',p/'probe.py')
 virtual='/tmp/'+p.name;env.update(HOME=virtual)
 actual=json.loads(subprocess.check_output(['unshare','--net','chroot','--userspec=101:101',str(T),'python3',virtual+'/probe.py','/usr',virtual],env=env,text=True,timeout=40));assert actual==expected
Path('/var/log/toddy/phase2/fast-float-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed UID101 exact CMake FastFloat8.2.10 discovery/header API consumer, float/double/trailing pointer/invalid/overflow/two reset-recovery cycles in private no-route namespace; architectureall/header-only SDK, no doctest/framework installed. Build prerequisite only, no VTE/terminal/GUI acceptance.','consumer':actual,'architecture':'all','test_framework_not_installed':True},indent=2)+'\n')
PY
