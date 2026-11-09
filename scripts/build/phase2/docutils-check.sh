#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess
p=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(p+['dpkg-query','-W','-f=${Status} ${Version}','docutils'],text=True)=='install ok installed 0.23-1+toddy1'
assert not subprocess.check_output(p+['dpkg','--audit'],text=True).strip();subprocess.run(p+['apt-get','check'],check=True)
r=subprocess.run(p+['python3','-'],input=Path('/opt/toddy-build/scripts/build/phase2/docutils-probe.py').read_text(),capture_output=True,text=True,env=env,check=True);proof=json.loads(r.stdout)
r=subprocess.run(p+['rst2man','--syntax-highlight=none'],input='toddy(1)\n========\n\nNAME\n----\n\nToddy offline.\n',capture_output=True,text=True,env=env,check=True);assert 'Toddy offline.' in r.stdout
assert subprocess.check_output(p+['python3','-c','import flit_core;print(flit_core.__version__)'],text=True,env=env).strip()=='4.0.2'
proof['installed_cli_exit']=0;proof['base_flit_unchanged']='4.0.2';Path('/var/log/toddy/phase2/docutils-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
