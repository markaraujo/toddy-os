#!/usr/bin/env python3
"""Check final-review source dependencies privately while the full suite runs."""
import base64
import hashlib
import json
import subprocess
import sys

from vm import ROOT, ssh_args


REMOTE = r'''
import base64,hashlib,json,pathlib,subprocess,sys,tempfile,types
P=pathlib.Path
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
for name,data in MODULES.items():
 module=types.ModuleType(name);module.__file__='/opt/toddy-build/scripts/build/'+name+'.py'
 sys.modules[name]=module
 exec(compile(base64.b64decode(data),module.__file__,'exec'),module.__dict__)
fixture=P('/mnt/lfs/sources/recovery/db-standard-nfv62s4o')
manifest=fixture/'inputs.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(manifest)=='336abd7ca1442e5102249da2f774b30326e06d268cd2b16b65fc81e8c333e6f9'
inputs=json.loads(manifest.read_text())
base=P(tempfile.mkdtemp(prefix='db-review-inputs-',dir='/mnt/lfs/tmp'))
private_sources=base/'sources';private_sources.mkdir()
(base/'config').mkdir()
for name,data in CONFIGS.items():(base/'config'/name).write_bytes(base64.b64decode(data))
shared=P('/mnt/lfs/sources')
names=['db5.3_5.3.28+dfsg2.orig.tar.xz','db5.3_5.3.28+dfsg2-12.debian.tar.xz',
       'db-5.3.28-test142-environment-1.patch','db-5.3.28-repmgr007-async-diagnostic-1.patch']
before={name:sha(shared/name) if (shared/name).exists() else None for name in names}
for name in names:
 if name in PATCHES:
  (private_sources/name).write_bytes(base64.b64decode(PATCHES[name]))
 else:
  assert (shared/name).is_file()
  (private_sources/name).symlink_to(shared/name)
 row=sys.modules['locked_inputs'].locked_source(base,name)
 assert row and sha(private_sources/name)==row['sha256'],name
verified=sys.modules['verify_db_tcl_tests'].verify(base,private_sources,fixture/'source')
assert len(verified)==483
for name,value in verified.items():assert inputs['source_files'][str(name)]=={'sha256':value},str(name)
seed=P('/var/log/toddy/build/h07-berkeley-db.recovery-seed.json')
assert sha(seed)=='75d8c0e77db2c0b42af7de2ff813e908ee4f2d5cc470dcb62bb5082013937e63'
native=json.loads(seed.read_text())['files']
assert len(native)==460
for name,value in native.items():
 assert sha(fixture/'source'/name)==value and inputs['source_files'][name]['sha256']==value,name
assert before=={name:sha(shared/name) if (shared/name).exists() else None for name in names}
assert sha(manifest)==inputs_sha
result={'private_reference':str(base),'frozen_tcl_files_verified':len(verified),
 'native_seed_files_verified':len(native),'shared_archives_unchanged':True,
 'shared_missing_patch_remains_absent':before[names[-1]] is None,
 'private_missing_patch_sha256':sha(private_sources/names[-1]),
 'input_manifest_sha256':sha(manifest),'full_suite_accepted':False,
 'global_build_inputs_synchronized':False,
 'module_sha256':{name:hashlib.sha256(base64.b64decode(data)).hexdigest() for name,data in MODULES.items()}}
(base/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
'''


def main():
    sys.path.insert(0, str(ROOT / 'scripts/build'))
    from locked_inputs import locked_source
    modules = {name: base64.b64encode((ROOT / 'scripts/build' / (name + '.py')).read_bytes()).decode()
               for name in ('locked_inputs', 'apply_db_test_fixture', 'verify_db_tcl_tests')}
    configs = {name: base64.b64encode((ROOT / 'config' / name).read_bytes()).decode()
               for name in ('sources.lock.json', 'security-overlay.lock.json', 'supplemental-sources.lock.json')}
    name = 'db-5.3.28-repmgr007-async-diagnostic-1.patch'
    patch = (ROOT / '.local/sources' / name).read_bytes()
    if hashlib.sha256(patch).hexdigest() != locked_source(ROOT, name)['sha256']:
        raise ValueError('Frozen local patch bytes differ')
    header = 'MODULES, CONFIGS, PATCHES, inputs_sha = ' + repr((modules, configs,
        {name: base64.b64encode(patch).decode()},
        '336abd7ca1442e5102249da2f774b30326e06d268cd2b16b65fc81e8c333e6f9')) + '\n'
    run = subprocess.run(ssh_args() + ['python3 -B -'], input=header + REMOTE,
                         text=True, capture_output=True, timeout=60)
    raw = (run.stdout + run.stderr).encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h07-db-review-inputs-' + sha + '.log')
    path.write_bytes(raw)
    if run.returncode:
        raise RuntimeError('Preserve final-review input failure: ' + str(path))
    print(run.stdout)
    print('EVIDENCE_SHA256 ' + sha)


if __name__ == '__main__':
    main()
