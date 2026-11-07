#!/usr/bin/env python3
"""Reverify the native recovery witness against its complete-suite input profile."""
import base64
import hashlib
import json
import subprocess

from vm import ROOT, ssh_args


REMOTE = r'''
import base64,copy,json,pathlib,sys,types
P=pathlib.Path
for name,data in MODULES.items():
    module=types.ModuleType(name);module.__file__='/opt/toddy-build/scripts/build/'+name+'.py'
    sys.modules[name]=module
    exec(compile(base64.b64decode(data),module.__file__,'exec'),module.__dict__)
review=sys.modules['db_coverage_result']
base=P('/mnt/lfs/sources/recovery/db-standard-coverage-0_05jaht')
standard=P('/mnt/lfs/sources/recovery/db-standard-nfv62s4o')
result=review.verify(base,standard)
record=json.loads((base/'result.json').read_text())
negatives=[]
for key,value in [('test_exit',1),('test_exit',False),('driver_exit',1),
                  ('inputs_unchanged',False),('diagnostic_cases_passed',False),
                  ('suite_accepted',True),('package_accepted',True),
                  ('records',{}),('command',['echo','fake']),('input_sha256','0'*64),
                  ('error','ignored failure')]:
    changed=copy.deepcopy(record);changed[key]=value
    try:review.validate_record(changed,base)
    except ValueError as error:negatives.append({'field':key,'reason':str(error)})
    else:raise AssertionError('Unverified coverage claim passed: '+key)
for label,candidate,pair in [('outside witness',P('/mnt/lfs'),standard),
                             ('witness paired to itself',base,base)]:
    try:review.verify(candidate,pair)
    except ValueError as error:negatives.append({'case':label,'reason':str(error)})
    else:raise AssertionError('Wrong evidence pairing accepted')
before=set(P('/mnt/lfs/tmp').glob('bdb-complete-review-*'))
for label,operation in [('unfinished full review',lambda:sys.modules['db_standard_review'].review(standard,base)),
                        ('strict full success gate',lambda:sys.modules['db_standard_result'].verify_completed(standard)),
                        ('coverage is not a full standard result',lambda:sys.modules['db_standard_result'].verify_completed(base))]:
    try:operation()
    except ValueError as error:negatives.append({'case':label,'reason':str(error)})
    else:raise AssertionError('An incomplete or focused run was accepted')
assert before==set(P('/mnt/lfs/tmp').glob('bdb-complete-review-*'))
print(json.dumps({'actual_native_witness':result,'negative_cases':negatives,
                  'native_reports_unchanged':True,'full_standard_run_accepted':False},indent=2))
'''


def main():
    names = ('db_standard_progress', 'db_standard_diagnostics', 'db_standard_result',
             'db_coverage_result', 'db_source_custody', 'db_standard_review')
    modules = {name: base64.b64encode((ROOT / 'scripts/build' / (name + '.py')).read_bytes()).decode()
               for name in names}
    run = subprocess.run(ssh_args() + ['python3 -B -'], input='MODULES=' + repr(modules) + '\n' + REMOTE,
                         text=True, capture_output=True, timeout=180)
    raw = (run.stdout + run.stderr).encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h07-db-coverage-verification-' + sha + '.json')
    path.write_bytes(raw)
    if run.returncode:
        raise RuntimeError('Preserve witness verification failure: ' + str(path))
    print(json.dumps(json.loads(run.stdout), indent=2))
    print('EVIDENCE_SHA256 ' + sha)


if __name__ == '__main__':
    main()
