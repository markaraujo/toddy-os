#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 - <<'PY'
from pathlib import Path
import json,re
base=Path('/mnt/lfs/sources/acl-2.4.0');results={}
for path in base.rglob('*.trs'):
 match=re.search(r'^:test-result: (\w+)$',path.read_text(),re.M)
 if match:results[str(path.relative_to(base))]=match[1]
assert len(results)>=13 and results.get('test/cp.trs')=='PASS',results
assert all(status in {'PASS','SKIP','XFAIL'} for status in results.values()),results
p=Path('/mnt/lfs/sources/evidence/h07-acl-final/classification.json')
p.write_text(json.dumps({'source':'LFS 13.1 section 8.27; full suite after final Coreutils','results':results,'temporary_cp_failure_reproduced':False},indent=2)+'\n')
print('Complete native ACL suite including cp.run passed without original bootstrap exception')
PY
