"""Run only pending original data cases after native hwdb integration; keep binaries."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(recipe,edid_log_sha256):
    assert os.getuid()==101
    w=Path('/build');out=w/'finish-2';out.mkdir()
    source=Path('/src/lib/colord/cd-test-private.c').read_text()
    cases=re.findall(r'g_test_add_func\s*\("([^"]+)"',source);assert len(cases)==38 and len(set(cases))==38
    reused=['/colord/spectrum','/colord/spectrum{planckian}','/colord/spectrum{subtract}','/colord/spectrum{cx}']
    original=(w/'compile/meson-logs/testlog.txt').read_text()
    for i,name in enumerate(reused,1):assert 'ok '+str(i)+' '+name in original
    binaries={str(p.relative_to(w)):sha(p) for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.read_bytes()[:4]==b'\x7fELF'}
    rows=[];env={**os.environ,'TESTDATADIR':'/src/data/tests','LD_LIBRARY_PATH':'/build/compile/lib/colord'}
    for i,name in enumerate(cases):
        if name in reused+['/colord/edid']:continue
        log=out/('%02d.log'%i)
        with log.open('xb') as f:r=subprocess.run(['/build/compile/lib/colord/colord-test-private','-p',name],env=env,stdout=f,stderr=subprocess.STDOUT)
        rows.append({'name':name,'native_exit':r.returncode,'log':str(log),'sha256':sha(log)})
        (out/'cases.json').write_text(json.dumps(rows,indent=2)+'\n')
        assert r.returncode==0,(name,r.returncode)
        text=log.read_text();assert 'ok 1 '+name in text and '# SKIP' not in text
    assert len(rows)==33
    tail='DESTDIR=/stage'+recipe.split('DESTDIR=/stage',1)[1]
    # The original summary describes a monolithic Meson run that failed before
    # hwdb integration. Preserve it; write the actual partitioned results below.
    tail=tail.split("python3 - <<'PY'",1)[0]
    subprocess.run(['/bin/bash','-euo','pipefail','-c',tail],check=True)
    assert binaries=={str(p.relative_to(w)):sha(p) for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.read_bytes()[:4]==b'\x7fELF'}
    proof={'scope':'Original Colord client/ICC/data cases across verified partitions, no color service/device acceptance','original_full_driver_exit':'SIGABRT before hwdb existed, retained; not reclassified as a passed monolithic run','original_cases_reused':reused,'native_edid_case_recovered':{'name':'/colord/edid','native_exit':0,'log_sha256':edid_log_sha256},'pending_case_results':rows,'distinct_original_cases_qualified':38,'compiled_elf_files_unchanged':len(binaries),'staged_consumer_exit':0,'profile':'Supported daemon=false client bootstrap for Mutter; no privileged color service/policy/sensor acceptance'}
    (w/'test-results.json').write_text(json.dumps(proof,indent=2)+'\n')
