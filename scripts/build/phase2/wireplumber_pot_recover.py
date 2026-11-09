"""Route generated POT to Meson's existing capture; reuse compiled native objects."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main(recipe):
    assert os.getuid()==101
    work=Path('/build');out=work/'pot-3';out.mkdir()
    ninja=work/'compile-2/build.ninja';before=ninja.read_bytes()
    old=b' -o ../../src/po/conf.pot '
    assert before.count(old)==1
    line=next(l for l in before.splitlines() if old in l)
    assert b'--capture po/conf.pot' in line and b'spa-json-po.py' in line
    preserved={}
    for p in (work/'compile-2').rglob('*'):
        if p.is_file() and not p.is_symlink():
            with p.open('rb') as f:
                if f.read(4)==b'\x7fELF':preserved[str(p.relative_to(work))]=hashlib.sha256(p.read_bytes()).hexdigest()
    assert preserved
    (out/'build.ninja.before').write_bytes(before)
    after=before.replace(old,b' ');ninja.write_bytes(after)
    body='ninja -C'+recipe.split('ninja -C',1)[1]
    body=body.replace('/build/compile','/build/compile-2').replace('/build/compile-2.log','/build/compile-3.log')
    (out/'finish.sh').write_text('set -euo pipefail\n'+body)
    (out/'routing.json').write_text(json.dumps({
        'scope':'Remove only source-output -o option from generated custom command; existing Meson capture writes private po/conf.pot. No source C/test/assertion or translations changed.',
        'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest(),
        'preserved_elfs':preserved,'original_compile_log':'compile-2.log','resume_compile_log':'compile-3.log'
    },indent=2)+'\n')
    subprocess.run(['bash',str(out/'finish.sh')],check=True)
    assert all(hashlib.sha256((work/n).read_bytes()).hexdigest()==h for n,h in preserved.items())
    proof_path=work/'test-results.json';proof=json.loads(proof_path.read_text())
    proof['generated_output_recovery']={'routing_record':'pot-3/routing.json','preserved_elfs_unchanged':len(preserved)}
    proof['optional_introspection']='Disabled: no frozen GNOME C/JS consumer needs Wp GI; no lxml/doc build dependency added'
    proof_path.write_text(json.dumps(proof,indent=2)+'\n')
