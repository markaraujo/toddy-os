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
result.update({'private_review_root':str(root),'refusals':negative,
 'reviewer_sha256':hashlib.sha256((root/'scripts/build/db_native_build_result.py').read_bytes()).hexdigest()})
(root/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('RESULT '+json.dumps(result))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / 'scripts/build'))
    from db_native_build_result import REQUIRED_CODE
    names = REQUIRED_CODE | {'scripts/build/db_native_build_result.py', 'scripts/build/db_standard_result.py'}
    files = {name: base64.b64encode((ROOT / name).read_bytes()).decode() for name in names}
    header = 'FILES, FIXTURE = ' + repr((files, args.fixture)) + '\n'
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
