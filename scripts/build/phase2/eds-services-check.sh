#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import json
r=json.loads(Path('/var/log/toddy/phase2/eds-installed-services-1.json').read_text())
assert r['uid']==101 and r['network_interfaces']==['lo'] and r['external_routes']==0
assert r['private_process_cleanup_verified'] and r['private_profile_removed']
assert all(row['exit']==0 for row in r['records'])
assert r['records'][0]['result']['created_and_read'] and r['records'][0]['result']['actual_disk_file_observed']
assert all(r['records'][1]['result'][k] for k in ['persisted_after_new_bus','precancelled_read_refused','post_cancel_recovery','removed_and_disk_state_verified'])
assert not Path('/mnt/lfs/tmp/toddy-eds-installed-services-1').exists()
PY
