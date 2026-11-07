#!/usr/bin/env python3
"""Verify native premature-qualification refusals without changing active inputs."""
import base64
import hashlib
import json
import subprocess

from vm import ROOT, ssh_args

REMOTE = r'''
import base64,hashlib,json,pathlib,subprocess,sys,tempfile,types
P=pathlib.Path
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
for name,data in MODULES.items():
 module=types.ModuleType(name);module.__file__='/opt/toddy-build/scripts/build/'+name+'.py'
 sys.modules[name]=module
 exec(compile(base64.b64decode(data),module.__file__,'exec'),module.__dict__)
full=P('/mnt/lfs/sources/recovery/db-standard-nfv62s4o')
coverage=P('/mnt/lfs/sources/recovery/db-standard-coverage-0_05jaht')
qualifier=sys.modules['db_standard_qualify']
custody=sys.modules['db_source_custody']
pid=int((full/'driver.pid').read_text());proc=P('/proc')/str(pid)
assert proc.exists() and (proc/'stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
assert str(full/'driver.py').encode() in (proc/'cmdline').read_bytes().split(b'\0')
def state(base):
 return {str(p):{'uid':p.stat().st_uid,'gid':p.stat().st_gid,'mode':p.stat().st_mode&0o777}
         for p in (base,base/'source')}
before=state(full)
reviews=set(P('/mnt/lfs/tmp').glob('bdb-complete-review-*'))
names=('source-custody.intent.json','source-custody.json','standard-qualification.json')
assert not any((full/name).exists() for name in names)
negatives=[]
for label,action in [('active full qualification',lambda:qualifier.qualify(full,coverage)),
                     ('active qualification verification',lambda:qualifier.verify_qualified(full)),
                     ('coverage cannot replace full suite',lambda:qualifier.qualify(coverage,coverage))]:
 try:action()
 except ValueError as error:negatives.append({'case':label,'reason':str(error)})
 else:raise AssertionError('Premature qualification accepted: '+label)
assert state(full)==before
assert not any((full/name).exists() for name in names)
assert reviews==set(P('/mnt/lfs/tmp').glob('bdb-complete-review-*'))
sealed=custody.seal_coverage(coverage,full)
proof=custody.verify_coverage_custody(coverage,full)
assert proof['custody_sealed'] and sealed['suite_accepted'] is False
records=P(tempfile.mkdtemp(prefix='bdb-qualification-record-',dir='/mnt/lfs/tmp'))
path=records/'probe.json'
custody.save(path,{'probe_only':True,'package_accepted':False})
original=path.read_bytes();inode=path.stat().st_ino
try:custody.save(path,{'package_accepted':True})
except FileExistsError:pass
else:raise AssertionError('Prior completed record was overwritten')
assert path.read_bytes()==original and path.stat().st_ino==inode and path.stat().st_mode&0o777==0o600
assert list(records.iterdir())==[path]
print(json.dumps({'actual_live_full_pid':pid,'full_metadata_unchanged':before,
 'no_full_custody_or_qualification_written':True,'no_review_directory_created':True,
 'negative_cases':negatives,'completed_coverage_proof':proof,
 'native_record_private':True,'native_record_overwrite_refused':True,'native_record_partial_names_cleaned':True,
 'module_sha256':{name:hashlib.sha256(base64.b64decode(data)).hexdigest() for name,data in MODULES.items()},
 'complete_positive_qualification_verified':False,'production_handoff_changed':False},indent=2))
'''


def main():
    names = ('db_standard_progress', 'db_standard_diagnostics', 'db_standard_result',
             'db_coverage_result', 'db_source_custody', 'db_standard_review', 'db_standard_qualify')
    modules = {name: base64.b64encode((ROOT / 'scripts/build' / (name + '.py')).read_bytes()).decode()
               for name in names}
    run = subprocess.run(ssh_args() + ['python3 -B -'],
                         input='MODULES=' + repr(modules) + '\n' + REMOTE,
                         text=True, capture_output=True, timeout=60)
    raw = (run.stdout + run.stderr).encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h07-db-qualification-gate-' + sha + '.json')
    path.write_bytes(raw)
    if run.returncode:
        raise RuntimeError('Preserve qualification gate failure: ' + str(path))
    print(run.stdout)
    print('EVIDENCE_SHA256 ' + sha)


if __name__ == '__main__':
    main()
