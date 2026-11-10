#!/bin/bash
# Reconcile installed recipe0/post1; never repeat the completed transaction.
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess
r=json.loads(Path('/var/log/toddy/build/b02-aspell-install.failed.json').read_text())
assert r['recipe_exit']==0 and r['postcheck_exit']==1
p=json.loads(Path('/var/log/toddy/packages/aspell_0.60.8.2-1+toddy1_amd64.json').read_text())
assert p['installed'] and p['archive_sha256']=='70368e76eaba8efe0c1195b7f23952eac5c5e49587ad1f9bc3df1df2e3735241'
archive=Path('/var/cache/toddy/packages/aspell_0.60.8.2-1+toddy1_amd64.deb')
with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==p['archive_sha256']
assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status} ${Version}','aspell'],text=True)=='install ok installed 0.60.8.2-1+toddy1'
print('Installed Aspell transaction reconciled; verification only, no package mutation.')
PY
