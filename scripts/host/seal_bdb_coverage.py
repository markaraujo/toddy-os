#!/usr/bin/env python3
"""Protect the completed native recovery witness without global input sync."""
import base64
import hashlib
import json
import subprocess

from vm import ROOT, ssh_args

REMOTE = r'''
import base64,json,pathlib,subprocess,sys,tempfile,types
P=pathlib.Path
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
for name,data in MODULES.items():
 module=types.ModuleType(name);module.__file__='/opt/toddy-build/scripts/build/'+name+'.py'
 sys.modules[name]=module
 exec(compile(base64.b64decode(data),module.__file__,'exec'),module.__dict__)
base=P('/mnt/lfs/sources/recovery/db-standard-coverage-0_05jaht')
standard=P('/mnt/lfs/sources/recovery/db-standard-nfv62s4o')
module=sys.modules['db_source_custody']
probe=P(tempfile.mkdtemp(prefix='bdb-custody-fd-',dir='/mnt/lfs/tmp'))
(probe/'held.txt').write_text('Actual descriptor boundary\n')
tree=module.snapshot(probe)
child=subprocess.Popen(['python3','-u','-c',
 'import sys; stream=open(sys.argv[1],"r+"); print("ready",flush=True); sys.stdin.read(1)',
 str(probe/'held.txt')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
try:
 assert child.stdout.readline().strip()=='ready'
 try:module.refuse_open_references(tree)
 except ValueError as error:held_refusal=str(error)
 else:raise AssertionError('A live held source descriptor was not detected')
finally:
 child.communicate('x',timeout=5)
assert child.returncode==0
module.refuse_open_references(tree)
try:module.seal_coverage(standard,standard)
except ValueError as error:negative=str(error)
else:raise AssertionError('Full-suite source was accepted as a coverage witness')
result=module.seal_coverage(base,standard)
assert module.seal_coverage(base,standard)==result
proof=module.verify_coverage_custody(base,standard)
assert proof['custody_sealed'] is True and proof['suite_accepted'] is False
attempt=subprocess.run(['chroot','/mnt/lfs','/usr/bin/python3','-c',
 'import os,pwd,sys; user=pwd.getpwnam("tester"); os.setgroups([]); os.setgid(user.pw_gid); os.setuid(user.pw_uid)\n'
 'try: open(sys.argv[1],"rb")\n'
 'except PermissionError: sys.exit(0)\n'
 'raise SystemExit("Unprivileged source is still readable")',
 '/'+str((base/'source/build-test/coverage-records.txt').relative_to('/mnt/lfs'))])
assert attempt.returncode==0
print(json.dumps({'custody_sealed':result['custody_sealed'],'suite_accepted':False,'package_accepted':False,
 'fixture':str(base),'source_entries':len(result['tree']),'unchanged_witness':result['witness'],
 'read_only_custody_proof':proof,
 'receipt_sha256':module.digest(base/'source-custody.json'),
 'intent_sha256':module.digest(base/'source-custody.intent.json'),
 'tester_read_denied':True,'repeat_seal_identical':True,'full_suite_refusal':negative,
 'actual_held_fd_refusal':held_refusal,'released_fd_check_passed':True},indent=2))
'''


def main():
    names = ('db_standard_progress', 'db_standard_diagnostics', 'db_standard_result',
             'db_coverage_result', 'db_source_custody')
    modules = {name: base64.b64encode((ROOT / 'scripts/build' / (name + '.py')).read_bytes()).decode()
               for name in names}
    run = subprocess.run(ssh_args() + ['python3 -B -'],
                         input='MODULES=' + repr(modules) + '\n' + REMOTE,
                         text=True, capture_output=True, timeout=60)
    raw = (run.stdout + run.stderr).encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h07-db-coverage-custody-' + sha + '.json')
    path.write_bytes(raw)
    if run.returncode:
        raise RuntimeError('Preserve custody transfer failure: ' + str(path))
    print(run.stdout)
    print('EVIDENCE_SHA256 ' + sha)


if __name__ == '__main__':
    main()
