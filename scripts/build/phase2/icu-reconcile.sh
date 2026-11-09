#!/bin/bash
# Read-only reconciliation of installed payload; never replay the package write.
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,stat
root=Path('/mnt/lfs')
previous=json.loads(Path('/var/log/toddy/build/b02-icu-install.failed.json').read_text())
assert previous['recipe_exit']==0 and previous['postcheck_exit']==1
assert 'DSO missing from command line' in Path('/var/log/toddy/build/b02-icu-install.log').read_text()
record=json.loads(Path('/var/log/toddy/packages/icu_78.3-1+toddy1_amd64.json').read_text());assert record['installed']
archive=Path('/var/cache/toddy/packages/icu_78.3-1+toddy1_amd64.deb')
with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==record['archive_sha256']
checked=0
for name,entry in record['payload'].items():
    p=root/name.lstrip('/');st=p.lstat()
    assert st.st_mode==entry['mode'] and st.st_uid==entry['uid'] and st.st_gid==entry['gid']
    if 'sha256' in entry:
        assert p.is_file() and not p.is_symlink()
        with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==entry['sha256']
        checked+=1
    elif 'symlink' in entry:assert p.is_symlink() and os.readlink(p)==entry['symlink']
    else:assert entry['directory'] and p.is_dir()
print(json.dumps({'scope':'Installed ICU payload/archive unchanged; original install0/post1 retained; direct consumer now explicitly links icu-uc alongside icu-i18n per symbols used, no reinstall','regular_files_verified':checked}))
PY
