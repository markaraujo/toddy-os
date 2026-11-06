#!/bin/bash
# Configuration correction requires rebuilding; preserve the original failure.
source /opt/toddy-build/scripts/build/h06/common.sh
python3 - <<'CHECK'
import json
from pathlib import Path
r=json.loads(Path('/var/log/toddy/build/h07-findutils.failed.json').read_text())
assert r['recipe_exit']==2 and r['changed_paths']==0
base=Path('/mnt/lfs/sources')
assert not (base/'stage/findutils').exists()
assert (base/'findutils-4.11.0/gnulib-tests/test-regex-el.log').is_file()
assert not (base/'recovery-findutils-system-regex').exists()
CHECK
mv "$LFS/sources/findutils-4.11.0" "$LFS/sources/recovery-findutils-system-regex"
bash /opt/toddy-build/scripts/build/h07/findutils.sh
