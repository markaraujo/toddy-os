#!/bin/bash
# Read-only reconciliation of installed payload; never replay the package write.
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,stat
root=Path('/mnt/lfs')
previous=json.loads(Path('/var/log/toddy/build/b02-gtk-install.failed.json').read_text())
assert previous['recipe_exit']==0 and previous['postcheck_exit']==1
assert previous['postcheck_sha256']=='3cb2b4200e1646ad5d0afbcbcf075f743b43896a19b966fe84e9f19eb190603d'
record=json.loads(Path('/var/log/toddy/packages/gtk_4.22.4-1+toddy1_amd64.json').read_text());assert record['installed']
archive=Path('/var/cache/toddy/packages/gtk_4.22.4-1+toddy1_amd64.deb')
with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==record['archive_sha256']=='71926defa7412777f080e97a4ad41ed49b328b272008caa5ddb3d9c8592c3b00'
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
print(json.dumps({'scope':'Installed GTK payload/archive unchanged; original install0/post1 retained, corrected GTK4 schema namespace postcheck only','regular_files_verified':checked}))
PY
