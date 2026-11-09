"""Inspect the exact built original test drivers without claiming test acceptance."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    assert os.getuid()==101
    root=Path('/build');out=root/'test-inventory';out.mkdir()
    commands=[('api-list',['/build/compile/dist/bin/jsapi-tests','--list']),('main-help',['python3','-B','/src/project/js/src/tests/jstests.py','--help']),('jit-help',['python3','-B','/src/project/js/src/jit-test/jit_test.py','--help'])]
    records=[]
    for name,args in commands:
        with (out/(name+'.stdout')).open('xb') as stdout,(out/(name+'.stderr')).open('xb') as stderr:r=subprocess.run(args,cwd='/build/compile',stdout=stdout,stderr=stderr,timeout=30)
        records.append({'name':name,'exit':r.returncode,'stdout_sha256':hashlib.sha256((out/(name+'.stdout')).read_bytes()).hexdigest()})
        assert r.returncode==0,'Inventory command failed, preserve actual output'
    artifacts={}
    for p in (root/'compile').rglob('*'):
        if not p.is_file() or p.is_symlink():continue
        with p.open('rb') as f:elf=f.read(4)==b'\x7fELF'
        if elf:
            with p.open('rb') as f:artifacts[str(p.relative_to(root))]=hashlib.file_digest(f,'sha256').hexdigest()
    (out/'compiled-artifacts-before.json').write_text(json.dumps(artifacts,sort_keys=True)+'\n')
    (out/'result.json').write_text(json.dumps({'scope':'Original built API test list and main/JIT supported arguments only; no suite acceptance','commands':records,'compiled_elf_artifacts':len(artifacts)},indent=2)+'\n')

if __name__=='__main__':main()
