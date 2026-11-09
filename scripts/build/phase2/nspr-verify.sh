#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,sys
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from qualify_nspr import qualify
qualify(Path('/opt/toddy-build'))
old=json.loads(Path('/var/log/toddy/build/b02-nspr-install.failed.json').read_text());assert old['recipe_exit']==0 and old['postcheck_exit']==1
receipt=json.loads(Path('/var/log/toddy/packages/nspr_4.40-1+toddy1_amd64.json').read_text());assert receipt['installed']
with Path('/var/cache/toddy/packages/nspr_4.40-1+toddy1_amd64.deb').open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==receipt['archive_sha256']
for name,row in receipt['payload'].items():
 p=Path('/mnt/lfs')/name.lstrip('/');st=p.lstat();assert (st.st_mode,st.st_uid,st.st_gid)==(row['mode'],row['uid'],row['gid'])
 if 'sha256' in row:
  with p.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==row['sha256']
 elif 'symlink' in row:assert p.is_symlink() and os.readlink(p)==row['symlink']
 else:assert row['directory'] and p.is_dir()
Path('/var/log/toddy/phase2/nspr-payload-verify-2.json').write_text(json.dumps({'payload_entries_unchanged':len(receipt['payload']),'archive_unchanged':True,'reinstalled':False,'original_failed_postcondition':'Own SDK version string assertion: upstream nspr.pc expands major.minor.patch as4.40.0; package version remains4.40'},indent=2)+'\n')
PY
