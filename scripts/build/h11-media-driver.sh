#!/bin/bash
# Resume only media assembly from an independently accepted H11 compression.
set -euo pipefail
cd /opt/toddy-build/scripts/build
prefix=/var/log/toddy/h11-media-driver
[[ ! -e $prefix.exit && ! -e $prefix.pid ]] || {
    echo 'Inspect and preserve the previous media attempt before retry' >&2
    exit 1
}
echo $$ > "$prefix.pid"
trap 'result=$?; echo "$result" > "$prefix.exit"' EXIT
python3 h11/require_gate.py
stage=/mnt/lfs/sources/stage
python3 -B - <<'PYVERIFY'
import fcntl,sys
from pathlib import Path
sys.path.insert(0,'h10')
from initramfs_input import physical,verify
root=Path('/mnt/lfs');parent=root/'sources/stage/h11-release-media'
with Path('/var/log/toddy/build/build.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    verify(root,root/'sources/stage/h11-release-compression/compression.json',True)
    if parent.exists() or parent.is_symlink():
        raise ValueError('Preserve existing media generation before retry')
    # The shared LFS /sources is sticky and owned by the build user. A nested
    # protected parent satisfies the strict existing media-input policy.
    parent.mkdir(mode=0o700)
    physical(root,parent,directory=True)
PYVERIFY
media_id=$(python3 - <<'PY'
import hashlib,json
from pathlib import Path
root = json.loads(Path('/mnt/lfs/sources/stage/h11-release-compression/compression.json').read_text())
kernel = hashlib.sha256(Path('/mnt/lfs/boot/vmlinuz-7.1.8-toddy').read_bytes()).hexdigest()
print(hashlib.sha256(('toddy-foundation-v1\n' + root['artifact_sha256'] + '\n' + kernel).encode()).hexdigest())
PY
)
python3 -B h10/initramfs_archive.py "$stage/h11-release-compression/compression.json" \
    "$stage/h11-release-media/initramfs" --media-id "$media_id" --release
python3 -B h11/assemble_iso.py "$stage/h11-release-media/initramfs/manifest.json" \
    "$stage/h11-release-media/iso"
