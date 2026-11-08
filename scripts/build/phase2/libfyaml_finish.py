"""Recover only the unit runner's private SDK loader path, no rebuilt binaries."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET


def summary(path):
    result={}
    for line in path.read_text().splitlines():
        if line.startswith('# ') and ':' in line:
            key,value=line[2:].split(':',1)
            if key in ['TOTAL','PASS','SKIP','XFAIL','FAIL','XPASS','ERROR']:result[key]=int(value.strip())
    return result


def main():
    assert os.getuid()==101 and not list(Path('/stage').iterdir())
    work=Path('/build');out=work/'finish-2';assert not out.exists();out.mkdir()
    cases=ET.parse(work/'check-ctest.xml').getroot().findall('.//testcase')
    assert len(cases)==9 and all(not any(c.find(k) is not None for k in ['failure','error','skipped']) for c in cases)
    tests=work/'compile/test';old=summary(tests/'test-suite.log')
    assert old=={'TOTAL':537,'PASS':535,'SKIP':0,'XFAIL':0,'FAIL':0,'XPASS':0,'ERROR':2}
    assert 'libcheck.so.0: cannot open shared object file' in (tests/'libfyaml.log').read_text()
    for name in ['test-suite.log','libfyaml.log','libfyaml.trs']:shutil.copy2(tests/name,out/('original-'+name))
    binaries={}
    for base in ['compile','check-compile']:
        for p in (work/base).rglob('*'):
            if p.is_file() and not p.is_symlink():
                with p.open('rb') as f:
                    if f.read(4)==b'\x7fELF':
                        f.seek(0);binaries[str(p.relative_to(work))]=hashlib.file_digest(f,'sha256').hexdigest()
    assert binaries;(out/'binaries-before.json').write_text(json.dumps(binaries,indent=2)+'\n')
    env=dict(os.environ,LD_LIBRARY_PATH='/build/test-sdk/lib',PKG_CONFIG_PATH='/build/test-sdk/lib/pkgconfig')
    def run(name,args,**kwargs):
        with (out/(name+'.log')).open('xb') as log:r=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,env=env,**kwargs)
        (out/(name+'.exit')).write_text(str(r.returncode)+'\n');assert r.returncode==0,(name,r.returncode)
    run('unit-recheck',['make','-C',str(tests),'check','TESTS=libfyaml.test'])
    unit=summary(tests/'test-suite.log');assert unit['TOTAL']>0 and unit['TOTAL']==unit['PASS']
    assert all(unit[k]==0 for k in ['SKIP','XFAIL','FAIL','XPASS','ERROR'])
    shutil.copy2(tests/'test-suite.log',out/'unit-test-suite.log');shutil.copy2(tests/'libfyaml.log',out/'unit-native.log')
    run('stage',['make','DESTDIR=/stage','install'],cwd=work/'compile')
    flags=subprocess.check_output(['pkg-config','--cflags','--libs','libfyaml'],env=dict(env,PKG_CONFIG_PATH='/stage/usr/lib/pkgconfig'),text=True).split()
    run('consumer-build',['cc','/src/toddy-probe.c','-I/stage/usr/include','-o',str(out/'native-yaml'),'-L/stage/usr/lib','-Wl,-rpath,/stage/usr/lib',*flags])
    run('consumer',[str(out/'native-yaml')])
    for name,digest in binaries.items():
        with (work/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
    result={'scope':'Native portable YAML parser; private SDK loader recovery only',
        'check_sdk_ctest_cases':9,'original_summary':old,'affected_unit_summary':unit,'reused_passed_cases':535,
        'existing_compiled_elf_files_unchanged':len(binaries),'staged_consumer_exit':0,
        'network_suites':'Explicitly disabled; no compiler network','reflection':'Optional libclang reflection disabled'}
    (work/'test-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
