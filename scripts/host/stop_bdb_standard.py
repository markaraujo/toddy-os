#!/usr/bin/env python3
"""Record owner-approved focused scope and stop only the identified standard run."""
import argparse
import hashlib
import subprocess
from vm import ROOT, ssh_args

REMOTE = r'''
import datetime,hashlib,json,os,pathlib,signal,time
P=pathlib.Path
base=P(FIXTURE)
assert base.resolve()==base and base.parent==P('/mnt/lfs/sources/recovery') and base.name.startswith('db-standard-')
assert base.stat().st_uid==0
record=json.loads((base/'running.json').read_text())
pid=record['test_process_pid'];driver=record['driver_pid']
proc=P('/proc')/str(pid)
assert proc.joinpath('cmdline').read_bytes().split(b'\0')[:-1]==[s.encode() for s in record['command']]
assert int(proc.joinpath('stat').read_text().rsplit(')',1)[1].split()[1])==driver
assert os.getpgid(pid)==pid
assert str(base/'driver.py').encode() in (P('/proc')/str(driver)/'cmdline').read_bytes()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
intent={'reason':'Owner explicitly approved focused delivery validation on 2026-11-07; ADR-0092',
 'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'driver':driver,'child':pid,
 'child_start_ticks':proc.joinpath('stat').read_text().rsplit(')',1)[1].split()[19],
 'running':record,'suite_accepted':False}
with (base/'owner-stop-intent.json').open('x') as f:
 os.fchmod(f.fileno(),0o600);json.dump(intent,f,indent=2);f.flush();os.fsync(f.fileno())
# Signal GNU timeout, which forwards to its own process group. The driver stays
# alive to collect the real exit code and immutable raw report copies.
os.kill(pid,signal.SIGTERM)
for _ in range(100):
 if (base/'driver.exit').exists():break
 time.sleep(.5)
report={'fixture':str(base),'intent_sha256':sha(base/'owner-stop-intent.json'),
 'suite_accepted':False,'classification':'owner-cancelled-incomplete',
 'driver_terminal':(base/'driver.exit').read_text().strip() if (base/'driver.exit').exists() else None,
 'test_terminal':(base/'test.exit').read_text().strip() if (base/'test.exit').exists() else None,
 'reports':{str(p.relative_to(base)):sha(p) for p in (base/'result-evidence').glob('*') if p.is_file()},
 'process_group_live':[]}
for path in P('/proc').iterdir():
 if not path.name.isdigit():continue
 try:
  fields=(path/'stat').read_text().rsplit(')',1)[1].split()
  if fields[0]!='Z' and int(fields[2])==pid:report['process_group_live'].append(int(path.name))
 except FileNotFoundError:pass
with (base/'owner-stop-result.json').open('x') as f:
 os.fchmod(f.fileno(),0o600);json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps(report,indent=2))
assert report['driver_terminal'] is not None and not report['process_group_live'],'Stop still pending; inspect before any shared mutation'
'''

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture')
    parser.add_argument('--owner-approved-focused-validation',action='store_true',required=True)
    args=parser.parse_args()
    run=subprocess.run(ssh_args()+['python3 -B -'],input='FIXTURE = '+repr(args.fixture)+'\n'+REMOTE,
                       text=True,capture_output=True,timeout=60)
    raw=(run.stdout+run.stderr).encode();digest=hashlib.sha256(raw).hexdigest()
    (ROOT/'.local/logs'/('h07-owner-stop-'+digest+'.json')).write_bytes(raw)
    print(raw.decode());print('EVIDENCE_SHA256 '+digest)
    if run.returncode:raise SystemExit(run.returncode)
if __name__=='__main__':main()
