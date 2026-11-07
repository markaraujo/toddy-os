#!/usr/bin/env python3
"""Verify a completed fresh native build using a private copy of reviewed code."""
import argparse
import base64
import hashlib
import json
import subprocess
import sys

from vm import ROOT, ssh_args

REMOTE = r'''
import base64,hashlib,json,pathlib,subprocess,sys,tempfile
P=pathlib.Path
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
root=P(tempfile.mkdtemp(prefix='db-native-review-',dir='/mnt/lfs/tmp'))
for name,encoded in FILES.items():
 path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
 path.write_bytes(base64.b64decode(encoded))
sys.path.insert(0,str(root/'scripts/build'))
import db_native_build_result as reviewer
base=P(FIXTURE)
result=reviewer.verify(base,reviewed_root=root)
negative=[]
for path in (P('/tmp'),P('/mnt/lfs/sources/recovery/db-standard-nfv62s4o')):
 try:reviewer.verify(path,reviewed_root=root)
 except ValueError as error:negative.append(str(error))
 else:raise AssertionError('Wrong build generation accepted')
recipe=root/'scripts/build/h07/berkeley-db-inner.sh'
original=recipe.read_bytes();recipe.write_bytes(original+b'\n# altered review copy\n')
try:
 try:reviewer.verify(base,reviewed_root=root)
 except ValueError as error:
  assert 'differs from reviewed code' in str(error)
  negative.append(str(error))
 else:raise AssertionError('Changed review recipe accepted')
finally:recipe.write_bytes(original)
if GATES:
 import db_standard_result as standard
 import db_source_custody as custody
 full=P('/mnt/lfs/sources/recovery/db-standard-nfv62s4o')
 prepared=P(result['prepared_standard_fixture'])
 coverage=P('/mnt/lfs/sources/recovery/db-standard-coverage-0_05jaht')
 pid=int((full/'driver.pid').read_text());proc=P('/proc')/str(pid)
 assert proc.exists() and (proc/'stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
 assert str(full/'driver.py').encode() in (proc/'cmdline').read_bytes().split(b'\0')
 state=lambda p:(p.stat().st_uid,p.stat().st_gid,p.stat().st_mode&0o777)
 before={str(p):state(p) for p in (full,full/'source',prepared,prepared/'source')}
 refusals=[]
 for label,action in (
   ('prepared fresh is not a completed suite',lambda:standard.verify_fresh_completed(prepared,base)),
   ('historical active suite remains unfinished',lambda:standard.verify_completed(full)),
   ('fresh profile cannot accept active full suite',lambda:standard.verify_fresh_completed(full,base)),
   ('prepared fresh is not historical completion',lambda:standard.verify_completed(prepared)),
   ('different native generation binding',lambda:standard.validate_fresh_binding(result,full,
     json.loads((full/'inputs.json').read_text()),standard.digest(full/'inputs.json')))):
  try:action()
  except ValueError as error:refusals.append({'case':label,'error':str(error)})
  else:raise AssertionError('Premature full standard result accepted: '+label)
 witness=custody.verify_coverage_custody(coverage,full)
 assert witness['custody_receipt_sha256']=='0a2b9b17cf57a0de76dc20ce426f784c4e92aa401d44a1d3f43817726e6dccb2'
 assert before=={str(p):state(p) for p in (full,full/'source',prepared,prepared/'source')}
 for fixture in (full,prepared):
  assert not (fixture/'standard-qualification.json').exists()
  assert not (fixture/'source-custody.json').exists()
 result.update({'full_standard_gate_refusals':refusals,'actual_live_full_pid':pid,
  'full_and_fresh_metadata_unchanged':True,'historical_coverage_custody':witness,
  'complete_positive_standard_result_verified':False,
  'standard_result_module_sha256':standard.digest(root/'scripts/build/db_standard_result.py')})
result.update({'private_review_root':str(root),'refusals':negative,
 'reviewer_sha256':hashlib.sha256((root/'scripts/build/db_native_build_result.py').read_bytes()).hexdigest()})
(root/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('RESULT '+json.dumps(result))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture')
    parser.add_argument('--unfinished-standard-gates', action='store_true', help='Check the current active/prepared standard refusals and retained coverage custody')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / 'scripts/build'))
    from db_native_build_result import REQUIRED_CODE
    names = REQUIRED_CODE | {'scripts/build/db_native_build_result.py', 'scripts/build/db_standard_result.py'}
    if args.unfinished_standard_gates:
        names |= {'scripts/build/' + name + '.py' for name in (
            'db_standard_progress', 'db_standard_diagnostics', 'db_coverage_result', 'db_source_custody')}
    files = {name: base64.b64encode((ROOT / name).read_bytes()).decode() for name in names}
    header = 'FILES, FIXTURE, GATES = ' + repr((files, args.fixture, args.unfinished_standard_gates)) + '\n'
    run = subprocess.run(ssh_args() + ['python3 -B -'], input=header + REMOTE,
                         capture_output=True, text=True, timeout=120)
    raw = (run.stdout + run.stderr).encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h07-native-db-verification-' + sha + '.log')
    path.write_bytes(raw)
    print(run.stdout + run.stderr)
    print('EVIDENCE_SHA256 ' + sha)
    if run.returncode:
        raise RuntimeError('Preserve native build verification: ' + str(path))


if __name__ == '__main__':
    main()
