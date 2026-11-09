"""Finish a skipped generated-data fixture and two pending cases, without replay."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(recipe,edid_log_sha256):
    assert os.getuid()==101
    w=Path('/build');out=w/'finish-3';out.mkdir()
    cases=re.findall(r'g_test_add_func\s*\("([^"]+)"',Path('/src/lib/colord/cd-test-private.c').read_text());assert len(cases)==38
    reused=['/colord/spectrum','/colord/spectrum{planckian}','/colord/spectrum{subtract}','/colord/spectrum{cx}']
    pending=[p for p in cases if p not in reused+['/colord/edid']];rows=json.loads((w/'finish-2/cases.json').read_text());assert len(rows)==31
    accepted={};skipped=[]
    for row in rows:
        log=Path(row['log']);assert row['native_exit']==0 and sha(log)==row['sha256']
        text=log.read_text();assert 'ok 1 '+row['name'] in text
        if '# SKIP' in text:skipped.append(row['name'])
        else:accepted[row['name']]=row
    assert len(accepted)==30 and skipped==['/colord/it8{cri-util}']
    binaries={str(p.relative_to(w)):sha(p) for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.read_bytes()[:4]==b'\x7fELF'}
    fixtures=w/'cri-fixtures';(fixtures/'run').mkdir(parents=True);(fixtures/'build').symlink_to('/build/compile',target_is_directory=True);(fixtures/'data').symlink_to('/src/data',target_is_directory=True)
    fixture_inputs={p:sha(fixtures/p) for p in ['build/data/cmf/CIE1931-2deg-XYZ.cmf','build/data/illuminant/CIE-F4.sp','data/ref/CIE-TCS.sp']}
    env={**os.environ,'TESTDATADIR':'/src/data/tests','LD_LIBRARY_PATH':'/build/compile/lib/colord'}
    for i,name in enumerate(pending):
        if name in accepted:continue
        log=out/('%02d.log'%i)
        with log.open('xb') as f:r=subprocess.run(['/build/compile/lib/colord/colord-test-private','-p',name],env=env,cwd=fixtures/'run',stdout=f,stderr=subprocess.STDOUT)
        row={'name':name,'native_exit':r.returncode,'log':str(log),'sha256':sha(log)};assert r.returncode==0,(name,r.returncode)
        text=log.read_text();assert 'ok 1 '+name in text and '# SKIP' not in text
        accepted[name]=row;(out/'new-cases.json').write_text(json.dumps(list(accepted.values()),indent=2)+'\n')
    assert len(accepted)==33 and not (w/'stage/usr').exists()
    tail='DESTDIR=/stage'+recipe.split('DESTDIR=/stage',1)[1];tail=tail.split("python3 - <<'PY'",1)[0]
    subprocess.run(['/bin/bash','-euo','pipefail','-c',tail],check=True)
    assert binaries=={str(p.relative_to(w)):sha(p) for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.read_bytes()[:4]==b'\x7fELF'}
    proof={'scope':'Original Colord client/ICC/data cases across verified partitions, no color service/device acceptance','original_full_driver_exit':'SIGABRT before hwdb existed, retained; not a passed monolithic run','original_cases_reused':reused,'native_edid_case_recovered':{'name':'/colord/edid','native_exit':0,'log_sha256':edid_log_sha256},'pending_case_results':[accepted[n] for n in pending],'distinct_original_cases_qualified':38,'compiled_elf_files_unchanged':len(binaries),'staged_consumer_exit':0,'fixture_recovery':{'original_skip':'generated files not available','current_case_exit':0,'inputs':fixture_inputs,'action':'Private expected relative-path layout points to unchanged existing generated/source data; no library/test/assertion patch or replay of accepted30cases'},'profile':'Supported daemon=false client bootstrap for Mutter; no privileged color service/policy/sensor acceptance'}
    (w/'test-results.json').write_text(json.dumps(proof,indent=2)+'\n')
