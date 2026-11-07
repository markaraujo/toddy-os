#!/usr/bin/env python3
"""Review the real terminal failed DB report without accepting its failures."""
import base64
import hashlib
import json
import subprocess

from vm import ROOT, ssh_args


REMOTE = r'''
import base64,hashlib,json,pathlib,sys,tempfile,types
P=pathlib.Path
for name,data in MODULES.items():
    module=types.ModuleType(name);module.__file__='/opt/toddy-build/scripts/build/'+name+'.py'
    sys.modules[name]=module
    exec(compile(base64.b64decode(data),name+'.py','exec'),module.__dict__)
review=sys.modules['db_standard_diagnostics']
root=P('/mnt/lfs')
base=P(tempfile.mkdtemp(prefix='bdb-terminal-diagnostics-',dir=root/'tmp'))
source=root/'sources/db-5.3.28'
record=json.loads(P('/var/log/toddy/build/h07-berkeley-db.failed.json').read_text())
assert record['recipe_exit']==1 and record['changed_paths']==0 and record['postcheck_exit'] is None
assert P('/var/log/toddy/h07-bdb-corrected-standard-driver.exit').read_text().strip()=='1'
assert json.loads(P('/var/log/toddy/build/h07-berkeley-db.manifest.json').read_text())=={}
assert review.digest(P('/var/log/toddy/build/h07-berkeley-db.log'))==record['log_sha256']
work=base/'review';work.mkdir(mode=0o700)
report=review.native_review(source,source/'build-test/ALL.OUT',
    root/'sources/evidence/h07-berkeley-db/standard.log',work)
assert report['unexpected_count']==25 and report['informational_count']==13
assert report['exact_diagnostic_profile'] and not report['unclassified']
assert len(report['actual_failures'])==2
try:
    review.require_diagnostic_profile(report)
except ValueError as error:
    report['original_qualification_refused']=str(error)
else:raise AssertionError('Original real failures were accepted')
handoff=sys.modules['db_standard_handoff']
handoff.validate_original(handoff.ORIGINAL)
report['exact_failed_original_can_be_archived']=True
before=set((P('/var/log/toddy/build')/'history').glob('*'))
assert not handoff.CANDIDATE.exists()
try:handoff.prepare(root/'sources/recovery/db-standard-nfv62s4o')
except ValueError as error:report['premature_production_handoff_refused']=str(error)
else:raise AssertionError('Incomplete corrected run received production nomination')
assert not handoff.CANDIDATE.exists() and before==set((P('/var/log/toddy/build')/'history').glob('*'))
live=root/'sources/recovery/db-standard-nfv62s4o/source/build-test/ALL.OUT'
try:
    review.complete_lines(live.read_text())
except ValueError as error:
    report['incomplete_corrected_summary_refused']=str(error)
else:raise AssertionError('Corrected state changed; inspect actual terminal result before repeating this probe')
report['fixture']=str(base)
(base/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
'''


def main():
    names = ('db_standard_progress', 'db_standard_diagnostics', 'db_standard_result', 'db_standard_handoff')
    modules = {name: base64.b64encode((ROOT / 'scripts/build' / (name + '.py')).read_bytes()).decode()
               for name in names}
    run = subprocess.run(ssh_args() + ['python3 -B -'],
                         input='MODULES=' + repr(modules) + '\n' + REMOTE,
                         text=True, capture_output=True, timeout=180)
    raw = (run.stdout + run.stderr).encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h07-db-terminal-diagnostics-' + sha + '.json')
    path.write_bytes(raw)
    if run.returncode:
        raise RuntimeError('Preserve diagnostic failure: ' + str(path))
    print(json.dumps(json.loads(run.stdout), indent=2))
    print('EVIDENCE_SHA256 ' + sha)


if __name__ == '__main__':
    main()
