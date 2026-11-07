#!/bin/bash
set -euo pipefail
cd /opt/toddy-build/scripts/build
python3 h11/require_gate.py
python3 -B - <<'PY'
import json
from pathlib import Path
from package_backend import PackageBackend
from stage_package import digest
root=Path('/mnt/lfs'); work=root/'sources/evidence/h11-python-qa-preparation'
plan=json.loads((work/'prepared.json').read_text())
transaction=json.loads((work/'transaction.json').read_text())
assert plan['installed_status_unchanged'] is True
assert transaction['complete'] is True
backend=PackageBackend()
for name,stem in zip(('python','python-test-support'),plan['successors']):
    record=json.loads((Path('/var/log/toddy/packages')/(stem+'.json')).read_text())
    assert record['installed'] is True
    state=backend.run('dpkg-query','-W','-f=${Version}\t${Status}',name,capture_output=True,text=True).stdout
    assert state==record['version']+'\tinstall ok installed'
    assert digest(Path('/var/cache/toddy/packages')/(stem+'.deb'))==record['archive_sha256']
audit=backend.run('dpkg','--audit',capture_output=True,text=True)
assert not audit.stdout.strip() and not audit.stderr.strip()
backend.run('apt-get','check')
print(json.dumps({'native_transaction_complete':True,'verification':transaction['verification'],
                  'native_dpkg_audit_empty':True,'apt_check_exit':0}))
PY
