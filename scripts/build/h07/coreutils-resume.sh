#!/bin/bash
# Preserve the partial pre-configure source, then retry the verified extraction.
source /opt/toddy-build/scripts/build/h06/common.sh
python3 - <<'CHECK'
import json
from pathlib import Path
r=json.loads(Path('/var/log/toddy/build/h07-coreutils.failed.json').read_text())
assert r['recipe_exit']==1 and r['changed_paths']==0
base=Path('/mnt/lfs/sources')
assert not (base/'stage/coreutils').exists()
assert not (base/'coreutils-9.11/Makefile').exists()
assert (base/'coreutils-9.11/src/sort.c.rej').is_file()
assert not (base/'recovery-coreutils-i18n-fuzz0').exists()
CHECK
mv "$LFS/sources/coreutils-9.11" "$LFS/sources/recovery-coreutils-i18n-fuzz0"
bash /opt/toddy-build/scripts/build/h07/coreutils.sh
