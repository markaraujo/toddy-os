"""Finish only the missing original API-map target and pending portable checks."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def main(recipe):
    assert os.getuid()==101
    w=Path('/build');out=w/'finish-2';out.mkdir()
    binaries={str(p.relative_to(w)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.read_bytes()[:4]==b'\x7fELF'}
    for name in ['testlog.txt','testlog.json']:
        shutil.copy2(w/'compile/meson-logs'/name,out/name)
    original=Path('/src/contrib/generate-version-script.py').read_text()
    assert original.count('key=parse_version')==1
    fixed=original.replace('key=parse_version','key=parse')
    (out/'generate-version-script.py').write_text(fixed)
    subprocess.run(['python3',str(out/'generate-version-script.py'),'LIBGUSB','/build/compile/gusb/GUsb-1.0.gir','/build/compile/gusb/libgusb.ver'],check=True)
    with (w/'upstream-tests-2.log').open('xb') as log:
        subprocess.run(['meson','test','-C','/build/compile','--no-rebuild','--print-errorlogs','gusb-exported-api'],stdout=log,stderr=subprocess.STDOUT,check=True)
    assert binaries=={str(p.relative_to(w)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.read_bytes()[:4]==b'\x7fELF'}
    tail=recipe.split("/build/compile/gusb/gusb-self-test -p",1)[1]
    tail='/build/compile/gusb/gusb-self-test -p'+tail
    subprocess.run(['/bin/bash','-euo','pipefail','-c',tail],check=True)
    p=w/'test-results.json';proof=json.loads(p.read_text());proof['recovery']='Build missing API-map test prerequisite explicitly, correct only remaining key=parse_version reference in private copy per frozen BLFS; API assertion unchanged, failed output retained, no accepted binary rebuild';proof['compiled_elf_files_unchanged']=len(binaries);proof['generator_before_sha256']=hashlib.sha256(original.encode()).hexdigest();proof['generator_after_sha256']=hashlib.sha256(fixed.encode()).hexdigest();p.write_text(json.dumps(proof,indent=2)+'\n')
