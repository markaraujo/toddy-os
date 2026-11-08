"""Resume existing native accessibility cache after adding DBus GIR metadata."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    assert os.getuid()==101 and Path('/usr/share/gir-1.0/DBus-1.0.gir').is_file()
    work=Path('/build');assert (work/'compile/build.ninja').is_file() and not list(Path('/stage').iterdir())
    assert not (work/'test-results.json').exists()
    out=work/'resume-2';out.mkdir();binaries={}
    for p in (work/'compile').rglob('*'):
        if p.is_file() and not p.is_symlink():
            with p.open('rb') as f:
                if f.read(4)==b'\x7fELF':
                    f.seek(0);binaries[str(p.relative_to(work/'compile'))]=hashlib.file_digest(f,'sha256').hexdigest()
    assert binaries;(out/'binaries-before.json').write_text(json.dumps(binaries,indent=2)+'\n')
    original=sys.argv[1];marker='ninja -C /build/compile -j4\n';assert original.count(marker)==1
    tail='set -euo pipefail\n'+marker+original.split(marker,1)[1]
    with (out/'remaining.log').open('xb') as log:r=subprocess.run(['bash','-c',tail],stdout=log,stderr=subprocess.STDOUT)
    (out/'remaining.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
    for relative,digest in binaries.items():
        with (work/'compile'/relative).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
    result=json.loads((work/'test-results.json').read_text());result['existing_compiled_elf_files_unchanged']=len(binaries)
    (work/'test-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
