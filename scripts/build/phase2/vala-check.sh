#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','vala'],text=True)=='install ok installed 0.56.19-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','libvala-0.56'],text=True).strip()=='0.56.19'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
assert not Path('/mnt/lfs/stage').exists()
with tempfile.TemporaryDirectory(prefix='toddy-vala-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);script=Path('/opt/toddy-build/scripts/build/phase2/vala-probe.py');shutil.copyfile(script,p/'probe.py')
    native='/tmp/'+p.name
    consumer=json.loads(subprocess.check_output(prefix+['python3','-B',native+'/probe.py','/',native+'/work'],env=env,text=True,timeout=120))
expected=json.loads(Path('/mnt/lfs/sources/phase2/work/vala-1/stage-results.json').read_text())['consumer'];assert consumer==expected
Path('/var/log/toddy/phase2/vala-installed-consumer.json').write_text(json.dumps({'scope':'Owned compiler SDK: actual native generated GObject/UTF8/signal/typed-error ABI, invalid source refusal/no executable/recovery, SDK/APT. Original1435passes reused; no IBus or native desktop acceptance.','consumer':consumer,'module_override_used':False},indent=2)+'\n')
PY
