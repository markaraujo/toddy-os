#!/bin/bash
# Fresh H10 validation generation. Each command owns the exclusive build lock.
set -euo pipefail
cd /opt/toddy-build/scripts/build
prefix=/var/log/toddy/h10-live-driver
[[ ! -e $prefix.exit && ! -e $prefix.pid ]] || {
    echo 'Inspect and preserve the previous live generation before retry' >&2
    exit 1
}
echo $$ > "$prefix.pid"
trap 'result=$?; echo "$result" > "$prefix.exit"' EXIT
python3 h10/require_gate.py
python3 - <<'PY'
import json
from pathlib import Path
for step in ('h10-squashfs-tools', 'h11-mtools', 'h11-libburn', 'h11-libisofs', 'h11-libisoburn'):
    result = json.loads((Path('/var/log/toddy/build') / (step + '.success.json')).read_text())
    assert result['recipe_exit'] == result['postcheck_exit'] == 0, step
for name in ('h10-live-root', 'h10-live-root-evidence', 'h10-live-compression',
             'h10-live-initramfs', 'h10-validation-iso'):
    path = Path('/mnt/lfs/sources/stage') / name
    assert not path.exists() and not path.is_symlink(), 'Preserve existing generation: ' + str(path)
PY
stage=/mnt/lfs/sources/stage
python3 -B h10/assemble_root.py "$stage/h10-live-root" "$stage/h10-live-root-evidence"
# Same frozen review date as the kernel build identity; no byte-identical OS claim.
epoch=$(python3 -c 'import datetime; print(int(datetime.datetime(2026,11,5,tzinfo=datetime.timezone.utc).timestamp()))')
python3 -B h10/compress_root.py "$stage/h10-live-root-evidence/assembly.json" \
    "$stage/h10-live-compression" --epoch "$epoch"
media_id=$(python3 - <<'PY'
import hashlib,json
from pathlib import Path
root = json.loads(Path('/mnt/lfs/sources/stage/h10-live-compression/compression.json').read_text())
kernel = hashlib.sha256(Path('/mnt/lfs/boot/vmlinuz-7.1.8-toddy').read_bytes()).hexdigest()
print(hashlib.sha256(('toddy-validation-v1\n' + root['artifact_sha256'] + '\n' + kernel).encode()).hexdigest())
PY
)
python3 -B h10/initramfs_archive.py "$stage/h10-live-compression/compression.json" \
    "$stage/h10-live-initramfs" --media-id "$media_id"
python3 -B h11/assemble_iso.py "$stage/h10-live-initramfs/manifest.json" \
    "$stage/h10-validation-iso" --validation
