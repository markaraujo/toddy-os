#!/bin/bash
# Preserve installed own archive; rerun all upstream tests and corrected CLI post.
source /opt/toddy-build/scripts/build/h06/common.sh
python3 "$SOURCE_TOOL" --verify-only triehash_0.3.orig.tar.gz
python3 - <<'PY'
import json,hashlib,subprocess
from pathlib import Path
record=json.loads(Path('/var/log/toddy/packages/triehash_0.3-1_all.json').read_text())
assert record['installed']
assert subprocess.check_output(['chroot','/mnt/lfs','/usr/bin/dpkg-query','-W','-f=${Status} ${Version}','triehash'],text=True)=='install ok installed 0.3-1'
for path,sha in [(Path('/var/cache/toddy/packages/triehash_0.3-1_all.deb'),record['archive_sha256']),
                 (Path('/mnt/lfs/usr/bin/triehash'),record['payload']['/usr/bin/triehash']['sha256'])]:
 with path.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==sha,path
print('Installed native Triehash archive/payload verified before full test rerun')
PY
chroot_run <<'INNER'
set -euo pipefail
cd /sources/triehash-0.3
su tester -c './tests/run-tests.sh' 2>&1 | tee /sources/evidence/h07-triehash/recovery-check.log
INNER
