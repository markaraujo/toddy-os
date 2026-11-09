#!/bin/bash
# Read-only reconciliation of installed payload; never replay the package write.
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,stat
root=Path('/mnt/lfs')
previous=json.loads(Path('/var/log/toddy/build/b02-pipewire-install.failed.json').read_text())
assert previous['recipe_exit']==0 and previous['postcheck_exit']==1
assert previous['postcheck_sha256']=='0b0293472b0adc44aee6ccab1abea6e93a2bfe92234c5ef0325d4f370c614c1c'
record=json.loads(Path('/var/log/toddy/packages/pipewire_1.6.8-1+toddy1_amd64.json').read_text());assert record['installed']
archive=Path('/var/cache/toddy/packages/pipewire_1.6.8-1+toddy1_amd64.deb')
with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==record['archive_sha256']=='6fcccccb584101ebf0899dcabbc64ff8551f8cc4e58356bc8878febc6a17c56a'
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
print(json.dumps({'scope':'Installed Pipewire payload/archive unchanged; original install0/post1 retained, builder setpriv before chroot userspec replaces absent native setpriv; postcheck only','regular_files_verified':checked}))
PY
