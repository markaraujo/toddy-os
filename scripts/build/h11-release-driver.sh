#!/bin/bash
# Fresh H11 release-profile generation. Each command owns the exclusive build lock.
set -euo pipefail
cd /opt/toddy-build/scripts/build
prefix=/var/log/toddy/h11-release-driver
[[ ! -e $prefix.exit && ! -e $prefix.pid ]] || {
    echo 'Inspect and preserve the previous live generation before retry' >&2
    exit 1
}
echo $$ > "$prefix.pid"
trap 'result=$?; echo "$result" > "$prefix.exit"' EXIT
python3 h11/require_gate.py
python3 - <<'PY'
import json
from pathlib import Path
for step in ('h11-python-qa', 'h10-squashfs-tools', 'h11-mtools', 'h11-libburn', 'h11-libisofs', 'h11-libisoburn'):
    result = json.loads((Path('/var/log/toddy/build') / (step + '.success.json')).read_text())
    assert result['recipe_exit'] == result['postcheck_exit'] == 0, step
for name in ('h11-release-root', 'h11-release-root-evidence', 'h11-release-compression',
             'h11-release-media'):
    path = Path('/mnt/lfs/sources/stage') / name
    assert not path.exists() and not path.is_symlink(), 'Preserve existing generation: ' + str(path)
PY
stage=/mnt/lfs/sources/stage
python3 -B h10/assemble_root.py "$stage/h11-release-root" "$stage/h11-release-root-evidence" --release
# Same frozen review date as the kernel build identity; no byte-identical OS claim.
epoch=$(python3 -c 'import datetime; print(int(datetime.datetime(2026,11,5,tzinfo=datetime.timezone.utc).timestamp()))')
python3 -B h10/compress_root.py "$stage/h11-release-root-evidence/assembly.json" \
    "$stage/h11-release-compression" --epoch "$epoch" --release
bash h11-media-driver.sh
