#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 "$SOURCE_TOOL" --verify-only systemd-261.2.tar.gz
python3 "$SOURCE_TOOL" --verify-only systemd-man-pages-261.2.tar.xz
python3 - <<'CHECK'
import json
from pathlib import Path
r=json.loads(Path('/var/log/toddy/build/h07-systemd.failed.json').read_text())
assert r['recipe_exit']==1
base=Path('/mnt/lfs/sources')
assert not (base/'stage/systemd').exists()
old=base/'evidence/h07-systemd/initial-POSIX/meson-logs/testlog.json'
rows=[json.loads(l) for l in old.read_text().splitlines()]
assert len(rows)==1862
assert sum(r['result']=='FAIL' for r in rows)==5
CHECK
install -m644 /opt/toddy-build/scripts/build/h07/evaluate-systemd.py "$LFS/sources/toddy-evaluate-systemd.py"
chroot_run < /opt/toddy-build/scripts/build/h07/systemd-test-install-inner.sh
# Book-order bootstrap still uses temporary util-linux libraries here.
# Add their final native dependency in the mandatory H07 metadata closure pass.
python3 /opt/toddy-build/scripts/build/stage_package.py systemd 261.2-1 \
 "$LFS/sources/stage/systemd" --depends 'glibc (>= 2.44-1), gcc-runtime, acl, libcap, kmod, xz, zstd, openssl' --source systemd-261.2.tar.gz --source systemd-man-pages-261.2.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/systemd-test-resume.sh --install
install -m644 /opt/toddy-build/scripts/build/h07/evaluate-systemd.py "$LFS/sources/toddy-evaluate-systemd.py"
chroot_run <<'INNER'
set -euo pipefail
systemd-machine-id-setup
systemctl preset-all
INNER
