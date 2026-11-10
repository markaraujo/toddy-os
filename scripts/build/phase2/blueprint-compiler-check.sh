#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess,tempfile,os,shutil,sys
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version} ${Architecture}','blueprint-compiler'],text=True)=='install ok installed 0.22.2-1+toddy1 all'
assert subprocess.check_output(prefix+['pkg-config','--modversion','blueprint-compiler'],text=True).strip()=='0.22.2'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_blueprint_compiler import qualify,digest
r=qualify(Path('/opt/toddy-build'))
for name,sha in r['stage_sha256'].items():assert digest(T/name)==sha
with tempfile.TemporaryDirectory(prefix='toddy-blueprint-',dir=T/'tmp') as directory:
 p=Path(directory);p.chmod(0o755);shutil.copyfile('/opt/toddy-build/scripts/build/phase2/blueprint-compiler-probe.py',p/'probe.py');virtual='/tmp/'+p.name
 actual=json.loads(subprocess.check_output(['chroot','--userspec=101:101',str(T),'python3',virtual+'/probe.py','/usr/bin/blueprint-compiler'],env=env,text=True,timeout=30));assert actual==r['consumer']
Path('/var/log/toddy/phase2/blueprint-compiler-installed-consumer.json').write_text(json.dumps({'scope':'Owned build-only architectureall compiler, installed stage bytes unchanged; actual UID101 CLI UTF8 GTK XML/invalid-property refusal/two recoveries/pkg-config/APT0. No display/widget/GNOME or full original suite acceptance.','consumer':actual,'installed_stage_files_identical':len(r['stage_sha256'])},indent=2)+'\n')
PY
