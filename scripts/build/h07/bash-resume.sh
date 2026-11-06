#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" --verify-only bash-5.3.tar.gz
python3 - <<'CHECK'
import json
from pathlib import Path
r=json.loads(Path('/var/log/toddy/build/h07-bash.failed.json').read_text())
assert r['recipe_exit']==1 and r['changed_paths']==0
assert not Path('/mnt/lfs/sources/stage/bash').exists()
CHECK
chroot_run < /opt/toddy-build/scripts/build/h07/bash-retest-inner.sh
python3 /opt/toddy-build/scripts/build/h07/evaluate-bash.py
chroot_run < /opt/toddy-build/scripts/build/h07/bash-install-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py bash 5.3-1 \
 "$LFS/sources/stage/bash" --depends 'glibc (>= 2.44-1), readline, ncurses' --source bash-5.3.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/bash-resume.sh --install
