#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp'}
receipt=json.loads(Path('/var/log/toddy/phase2/hwdb-cache-transaction.json').read_text());assert receipt['state']=='complete'
base='/sources/phase2/';code=['chroot','--userspec=101:101','/mnt/lfs',base+'work/colord-1/compile/lib/colord/colord-test-private','-p','/colord/edid']
env.update(TESTDATADIR=base+'inputs/colord-1.4.8/data/tests',LD_LIBRARY_PATH=base+'work/colord-1/compile/lib/colord')
with Path('/var/log/toddy/phase2/hwdb-colord-edid-2.log').open('xb') as out:r=subprocess.run(code,env=env,stdout=out,stderr=subprocess.STDOUT)
assert r.returncode==0
assert 'ok 1 /colord/edid' in Path('/var/log/toddy/phase2/hwdb-colord-edid-2.log').read_text()
Path('/var/log/toddy/phase2/hwdb-cache-installed-consumer.json').write_text(json.dumps({'scope':'Native owned hardware database vendor/refusal API/CLI and unchanged original Colord EDID fixture; no physical device test','native_consumer_exit':0,'original_colord_edid_case_exit':0,'old_nonlegal_regular_files_unchanged':receipt['old_nonlegal_regular_files_unchanged']},indent=2)+'\n')
PY
