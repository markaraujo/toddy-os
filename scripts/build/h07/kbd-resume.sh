#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 - <<'CHECK'
import json
from pathlib import Path
r=json.loads(Path('/var/log/toddy/build/h07-kbd.failed.json').read_text())
assert r['recipe_exit']==1 and r['changed_paths']==0
base=Path('/mnt/lfs/sources')
assert not (base/'stage/kbd').exists()
assert (base/'kbd-2.10.0/data/keymaps/i386/fgGIod/tr_f-latin5.map.rej').is_file()
assert not (base/'recovery-kbd-backspace-context').exists()
CHECK
mv "$LFS/sources/kbd-2.10.0" "$LFS/sources/recovery-kbd-backspace-context"
bash /opt/toddy-build/scripts/build/h07/kbd.sh
