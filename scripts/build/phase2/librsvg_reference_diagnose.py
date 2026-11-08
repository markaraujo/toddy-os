"""Retain only the failing compiled reference's pixels; not acceptance/rebuild."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    assert os.getuid()==101 and Path('/build/upstream-tests.exit').read_text().strip()=='1'
    if sys.argv[1:]==['--resume-manifest']:
        assert 'Manifest directory unknown: NotPresent' in Path('/build/reference-diagnose-2/test.log').read_text()
        output=Path('/build/reference-diagnose-3')
    else:
        assert not sys.argv[1:]
        output=Path('/build/reference-diagnose-3')
    output.mkdir()
    def binaries():
        result={}
        for p in Path('/build/compile').rglob('*'):
            if not p.is_file() or p.is_symlink():continue
            with p.open('rb') as f:
                if f.read(4)!=b'\x7fELF':continue
                f.seek(0);result[str(p.relative_to('/build/compile'))]=hashlib.file_digest(f,'sha256').hexdigest()
        return result
    before=binaries();assert before
    (output/'binaries-before.json').write_text(json.dumps(before,indent=2)+'\n')
    matches=list(Path('/build/compile/target/release/deps').glob('reference-*'))
    matches=[p for p in matches if p.is_file() and os.access(p,os.X_OK) and not p.suffix]
    assert len(matches)==1
    command=[str(matches[0]),'--exact','tests::svg1_1_text_text_03_b_svg','--include-ignored','--nocapture']
    with (output/'test.log').open('xb') as log:
        r=subprocess.run(command,cwd='/build/source/rsvg',env=dict(os.environ,CARGO_MANIFEST_DIR='/build/source/rsvg',TESTS_OUTPUT_DIR=str(output/'pixels')),stdout=log,stderr=subprocess.STDOUT)
    (output/'test.exit').write_text(str(r.returncode)+'\n')
    after=binaries();assert after==before
    assert r.returncode==101 and '0 passed; 1 failed;' in (output/'test.log').read_text()
    assert len(list((output/'pixels').glob('*.png')))==2
    proof={'scope':'Single already compiled upstream golden failure reproduced for pixel diagnosis only, not renderer acceptance',
           'native_exit':r.returncode,'command':command,'unchanged_elf_files':len(before),'golden_passed':False}
    (output/'results.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))


if __name__=='__main__':main()
