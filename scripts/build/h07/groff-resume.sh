#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 "$SOURCE_TOOL" --verify-only groff-1.24.1.tar.gz
python3 - <<'CHECK'
import json
from pathlib import Path
r=json.loads(Path('/var/log/toddy/build/h07-groff.failed.json').read_text())
assert r['recipe_exit']==2 and r['changed_paths']==0
base=Path('/mnt/lfs/sources/groff-1.24.1')
assert (base/'eqn').is_file() and (base/'Makefile').is_file()
assert 'exec: eqn: not found' in (base/'src/preproc/eqn/tests/neqn-smoke-test.sh.log').read_text()
assert not Path('/mnt/lfs/sources/stage/groff').exists()
CHECK
chroot_run < /opt/toddy-build/scripts/build/h07/groff-test-install-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py groff 1.24.1-1 \
 "$LFS/sources/stage/groff" --depends 'glibc (>= 2.44-1), gcc-runtime, perl' --source groff-1.24.1.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/groff-resume.sh --install
