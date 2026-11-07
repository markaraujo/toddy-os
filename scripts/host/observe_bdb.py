#!/usr/bin/env python3
"""Observe the original and corrected BDB runs without changing guest files."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

from vm import ROOT, ssh_args


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corrected-fixture', required=True)
    args = parser.parse_args()
    fixture = Path(args.corrected_fixture)
    if fixture.parent != Path('/mnt/lfs/sources/recovery') or not fixture.name.startswith('db-standard-'):
        raise ValueError('Supply the exact active corrected standard fixture')
    module = (ROOT / 'scripts/build/db_standard_progress.py').read_bytes()
    remote = 'MODULE=' + repr(base64.b64encode(module).decode()) + '\nFIXTURE=' + repr(str(fixture)) + '\n' + r'''
import base64,datetime,json
from pathlib import Path
scope={'__name__':'read_only_progress'}
exec(compile(base64.b64decode(MODULE),'db_standard_progress.py','exec'),scope)
base=Path(FIXTURE)
assert base.resolve()==base and base.stat().st_uid==0
runs={}
for name,pidfile,marker,source,outer,exits in (
 ('original',Path('/var/log/toddy/h07-bdb-corrected-standard-driver.pid'),
  'h07-bdb-corrected-standard-driver',Path('/mnt/lfs/sources/db-5.3.28'),
  Path('/mnt/lfs/sources/evidence/h07-berkeley-db/standard.log'),
  [Path('/var/log/toddy/h07-bdb-corrected-standard-driver.exit')]),
 ('corrected',base/'driver.pid',str(base/'driver.py'),base/'source',base/'standard.log',
  [base/'test.exit',base/'driver.exit'])):
 pid=int(pidfile.read_text());proc=Path('/proc')/str(pid);live=proc.exists();start=None
 if live:
  cmd=(proc/'cmdline').read_bytes().decode().replace('\0',' ')
  if marker not in cmd:raise ValueError('PID identity differs: '+name)
  state=(proc/'stat').read_text().rsplit(')',1)[1].split();live=state[0]!='Z';start=int(state[19])
 result=scope['observe'](source,outer,source/'build-test/ALL.OUT')
 result.update(pid=pid,live=live,start_ticks=start,
  terminal_exits={str(path):path.read_text().strip() if path.exists() else None for path in exits})
 runs[name]=result
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runs':runs},indent=2))
'''
    run = subprocess.run(ssh_args() + ['python3 -B -'], input=remote, text=True,
                         capture_output=True, timeout=60)
    if run.returncode:
        raise RuntimeError(run.stdout + run.stderr)
    raw = run.stdout.encode()
    report = json.loads(raw)
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h07-db-standard-progress-' + sha + '.json')
    path.write_bytes(raw)
    # Preserve full header snapshots in evidence, keep routine output concise.
    for row in report['runs'].values():
        del row['outer_log_snapshot']
    print(json.dumps(report, indent=2))
    print('EVIDENCE_SHA256 ' + sha)


if __name__ == '__main__':
    main()
