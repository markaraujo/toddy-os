"""Resume the existing Mutter build after unchanged upstream GL GIR delivery."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def binaries():
    result={}
    for p in Path('/build/compile').rglob('*'):
        if not p.is_file() or p.is_symlink():continue
        with p.open('rb') as f:head=f.read(4)
        if head==b'\x7fELF':result[str(p.relative_to('/build'))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return result

def main(recipe):
    assert os.getuid()==101
    w=Path('/build');assert not (w/'compile-2.log').exists()
    assert "Couldn't find include 'GL-1.0.gir'" in (w/'compile.log').read_text()
    assert hashlib.sha256(Path('/usr/share/gir-1.0/GL-1.0.gir').read_bytes()).hexdigest()=='3a45fd8a802c84ac66099d10f7f64a89a28f678be623f6fde61962e0924db849'
    before=binaries();assert before;(w/'compiled-before-resume.json').write_text(json.dumps(before,indent=2)+'\n')
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    with (w/'compile-2.log').open('xb') as log:subprocess.run(['ninja','-C','/build/compile','-j4'],stdout=log,stderr=subprocess.STDOUT,check=True)
    after=binaries();assert all(after.get(p)==sha for p,sha in before.items()),'Existing compiled artifact changed; inspect before accepting'
    tail='meson test -C'+recipe.split('meson test -C',1)[1]
    subprocess.run(['/bin/bash','-euo','pipefail','-c',tail],check=True)
    p=w/'test-results.json';d=json.loads(p.read_text());d['compile_recovery']='Add original same-version upstream GL GIR/typelib component, resume existing Ninja directory; no source/library foundation rebuild';d['existing_compiled_elf_files_unchanged']=len(before);p.write_text(json.dumps(d,indent=2)+'\n')
