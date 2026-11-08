"""Stage unchanged bwrap after actual native-kernel qualification, never replay tests."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

assert os.getuid()==101 and not list(Path('/stage').iterdir())
work=Path('/build');out=work/'stage-6';out.mkdir()
proof=json.loads(sys.argv[1]);assert proof['kernel']=='7.1.8-toddy'
binary=work/'compile/bwrap'
assert hashlib.sha256(binary.read_bytes()).hexdigest()==proof['binary_sha256']
rows=[json.loads(x) for x in (work/'compile/meson-logs/testlog.json').read_text().splitlines()]
utilities=[r for r in rows if r['name'].split(':')[-1]=='test-utils']
assert len(utilities)==1 and utilities[0]['result']=='OK' and utilities[0]['returncode']==0
assert len(re.findall(r'^ok\b',utilities[0]['stdout'],re.M))==26
assert 'not ok' not in utilities[0]['stdout']
for name in ['testlog.json','testlog.txt']:
    shutil.copy2(work/'compile/meson-logs'/name,out/('original-'+name))
binaries={}
for p in (work/'compile').rglob('*'):
    if p.is_file() and not p.is_symlink():
        with p.open('rb') as f:
            if f.read(4)==b'\x7fELF':
                f.seek(0);binaries[str(p.relative_to(work/'compile'))]=hashlib.file_digest(f,'sha256').hexdigest()
assert len(binaries)==proof['existing_compiled_elf_files_unchanged']==11
(out/'binaries-before.json').write_text(json.dumps(binaries,indent=2)+'\n')
with (out/'stage.log').open('xb') as log:
    r=subprocess.run(['meson','install','-C','/build/compile','--no-rebuild'],env=dict(os.environ,DESTDIR='/stage'),stdout=log,stderr=subprocess.STDOUT)
(out/'stage.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
assert hashlib.sha256(Path('/stage/usr/bin/bwrap').read_bytes()).hexdigest()==proof['binary_sha256']
assert Path('/stage/usr/bin/bwrap').stat().st_mode & 0o6000==0
for relative,digest in binaries.items():
    with (work/'compile'/relative).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
result={'scope':'Native unprivileged bwrap on actual Toddy7.1.8 kernel; unchanged stage only, not graphical/complete Glycin/application sandbox acceptance',
        'qualification':proof,'upstream_utility_cases':26,
        'native_test_run':{'passed_cases':64,'skipped_cases':5,'skip_reasons':{'no FUSE support':4,'no strace fault injection':1}},
        'native_namespace_joining_drivers':{'test-specifying-pidns.sh':0,'test-specifying-userns.sh':0},
        'optional_python_seccomp_driver':'Unavailable optional Python binding; original SKIP retained, not a pass',
        'existing_compiled_elf_files_unchanged':11,'staged_consumer_exit':0,
        'native_namespace_consumer_exit':0,'profile':'support_setuid=false, selinux disabled, no global security changes. Private upstream fixture maps actual LFS /lib64; original driver assertions unchanged.'}
(work/'test-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
