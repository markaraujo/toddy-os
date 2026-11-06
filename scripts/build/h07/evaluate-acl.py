#!/usr/bin/env python3
"""Keep ACL cp.run's documented book-order limitation distinct from other faults."""
import json
from pathlib import Path
import re

base = Path('/mnt/lfs/sources/acl-2.4.0')
folder = Path('/mnt/lfs/sources/evidence/h07-acl')
results = {}
for path in base.rglob('*.trs'):
    match = re.search(r'^:test-result: (\w+)$', path.read_text(), re.M)
    if match:
        results[str(path.relative_to(base))] = match[1]
unknown = {name: status for name, status in results.items()
           if status not in ('PASS', 'SKIP', 'XFAIL')
           and not (name == 'test/cp.trs' and status == 'FAIL')}
exit_code = int((folder / 'check.exit').read_text())
accepted = (len(results) >= 13 and 'PASS' in results.values() and not unknown
            and exit_code in (0, 2))
if exit_code != 0 and results.get('test/cp.trs') != 'FAIL':
    accepted = False
record = {'results': results, 'suite_exit': exit_code, 'unexplained': unknown,
          'source': 'LFS 13.1-systemd 8.27: cp.run fails before Coreutils ACL support',
          'accepted': accepted}
(folder / 'classification.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record))
if not accepted:
    raise SystemExit('ACL suite not accepted; inspect original reports')
