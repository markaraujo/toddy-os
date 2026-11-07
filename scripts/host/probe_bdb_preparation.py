#!/usr/bin/env python3
"""Exercise versioned preparation with completed native inputs, never run_std."""
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
root=P(tempfile.mkdtemp(prefix='db-prepare-code-',dir='/mnt/lfs/tmp'))
for name,data in FILES.items():
 path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
 path.write_bytes(base64.b64decode(data))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0,str(root/'scripts/build'))
import db_standard_prepare as prepare
from locked_inputs import locked_source
sources=root/'sources';sources.mkdir()
shared=P('/mnt/lfs/sources')
for name in ('db5.3_5.3.28+dfsg2.orig.tar.xz','db5.3_5.3.28+dfsg2-12.debian.tar.xz',
             'db-5.3.28-test142-environment-1.patch','db-5.3.28-repmgr007-async-diagnostic-1.patch'):
 if name.endswith('repmgr007-async-diagnostic-1.patch'):
  (sources/name).write_bytes(base64.b64decode(PATCH))
 else:(sources/name).symlink_to(shared/name)
 assert sha(sources/name)==locked_source(root,name)['sha256']
fixture=shared/'recovery/db-standard-coverage-0_05jaht'
full=shared/'recovery/db-standard-nfv62s4o'
assert (fixture/'driver.exit').read_text().strip()=='0'
assert sha(fixture/'source-custody.json')=='0a2b9b17cf57a0de76dc20ce426f784c4e92aa401d44a1d3f43817726e6dccb2'
assert sha(full/'inputs.json')=='336abd7ca1442e5102249da2f774b30326e06d268cd2b16b65fc81e8c333e6f9'
protected=['source-custody.json','source-custody.intent.json','inputs.json','result.json']
before={name:sha(fixture/name) for name in protected}
recovery=shared/'recovery'
negative=[]
for source in (P('/tmp'),shared/'db-5.3.28'):
 generations=set(recovery.glob('db-standard-*'))
 try:prepare.prepare(source,root=root,sources=sources)
 except (ValueError,SystemExit) as error:negative.append({'source':str(source),'error':str(error)})
 else:raise AssertionError('Invalid source was accepted')
 assert set(recovery.glob('db-standard-*'))==generations
result=prepare.prepare(fixture/'source',root=root,sources=sources)
prepared=P(result['fixture'])
assert (prepared/'source/build-production').is_dir()
assert not list((prepared/'source/build-production').iterdir())
seed=P('/var/log/toddy/build/h07-berkeley-db.recovery-seed.json')
assert sha(seed)=='75d8c0e77db2c0b42af7de2ff813e908ee4f2d5cc470dcb62bb5082013937e63'
files=json.loads(seed.read_text())['files']
for name,value in files.items():assert sha(prepared/'source'/name)==value,name
assert before=={name:sha(fixture/name) for name in protected}
assert sha(full/'inputs.json')=='336abd7ca1442e5102249da2f774b30326e06d268cd2b16b65fc81e8c333e6f9'
assert not (prepared/'running.json').exists() and not (prepared/'driver.pid').exists()
assert not (prepared/'standard.log').exists() and not (prepared/'source/build-test/ALL.OUT').exists()
result.update({'private_code_root':str(root),'negative_checks':negative,
 'verified_native_seed_files':len(files),'completed_coverage_records_unchanged':True,
 'active_full_input_manifest_unchanged':True,'global_build_inputs_synchronized':False,
 'preparation_module_sha256':sha(root/'scripts/build/db_standard_prepare.py')})
(root/'native-probe-result.json').write_text(json.dumps(result,indent=2)+'\n')
print('RESULT '+json.dumps(result))
'''


def main():
    sys.path.insert(0, str(ROOT / 'scripts/build'))
    from locked_inputs import locked_source
    names = ['scripts/build/' + name + '.py' for name in
             ('db_standard_prepare', 'verify_db_tcl_tests', 'locked_inputs', 'apply_db_test_fixture')]
    names += ['scripts/build/h07/' + name for name in (
        'berkeley-db-standard-regression.tcl', 'berkeley-db-isolated-tests.sh',
        'berkeley-db-isolation-probe.py', 'berkeley-db-isolated-driver.py')]
    names += ['config/' + name for name in (
        'sources.lock.json', 'security-overlay.lock.json', 'supplemental-sources.lock.json')]
    files = {name: base64.b64encode((ROOT / name).read_bytes()).decode() for name in names}
    name = 'db-5.3.28-repmgr007-async-diagnostic-1.patch'
    patch = (ROOT / '.local/sources' / name).read_bytes()
    if hashlib.sha256(patch).hexdigest() != locked_source(ROOT, name)['sha256']:
        raise ValueError('Frozen local patch changed')
    header = 'FILES, PATCH = ' + repr((files, base64.b64encode(patch).decode())) + '\n'
    run = subprocess.run(ssh_args() + ['python3 -B -'], input=header + REMOTE,
                         capture_output=True, text=True, timeout=240)
    raw = (run.stdout + run.stderr).encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h07-db-preparation-' + sha + '.log')
    path.write_bytes(raw)
    print(run.stdout)
    print('EVIDENCE_SHA256 ' + sha)
    if run.returncode:
        raise RuntimeError('Preserve private preparation failure: ' + str(path))


if __name__ == '__main__':
    main()
