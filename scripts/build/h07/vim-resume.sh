#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 - <<'CHECK'
from pathlib import Path
import json
r=json.loads(Path('/var/log/toddy/build/h07-vim.failed.json').read_text())
assert r['recipe_exit']==2 and r['changed_paths']==0
base=Path('/mnt/lfs/sources')
assert not (base/'stage/vim').exists()
assert not (base/'recovery-vim-nonpty').exists()
assert (base/'evidence/h07-vim/initial-nonpty-test-reports.tar.gz').is_file()
log=(base/'vim-9.2.1201/src/testdir/messages').read_text()
assert 'Executed Test_getchar()' in log and 'Executed Test_ex_mode_with_global()' in log
assert 'FAILED' not in log
CHECK
mkdir -p "$LFS/sources/evidence/h07-vim/initial-nonpty"
cp "$LFS/sources/evidence/h07-vim/check.log" "$LFS/sources/evidence/h07-vim/download-events.jsonl" "$LFS/sources/evidence/h07-vim/initial-nonpty/"
mv "$LFS/sources/vim-9.2.1201" "$LFS/sources/recovery-vim-nonpty"
bash /opt/toddy-build/scripts/build/h07/vim.sh
