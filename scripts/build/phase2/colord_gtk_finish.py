"""Finish the existing ABI build after a source-backed optional VAPI correction."""
from pathlib import Path
import hashlib,json,subprocess

def artifacts():
 w=Path('/build/compile')
 return {str(p.relative_to(w)):hashlib.sha256(p.read_bytes()).hexdigest() for p in w.rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'}

def main(recipe):
 w=Path('/build');assert not (w/'before-finish-2.json').exists()
 assert 'Package `colord' in (w/'original-build.log').read_text() and 'not found' in (w/'original-build.log').read_text()
 before=artifacts();assert before
 (w/'before-finish-2.json').write_text(json.dumps(before,indent=2)+'\n')
 subprocess.run(['meson','configure','/build/compile','-Dvapi=false'],check=True)
 with (w/'finish-build-2.log').open('xb') as log:
  subprocess.run(['ninja','-C','/build/compile','-j4'],stdout=log,stderr=subprocess.STDOUT,check=True)
 assert artifacts()==before,'Existing ABI/test ELFs changed: investigate before acceptance'
 assert recipe.count('meson introspect /build/compile --tests')==1
 suffix=recipe[recipe.index('meson introspect /build/compile --tests'):]
 subprocess.run(['bash','-euo','pipefail','-c',suffix],check=True)
 assert artifacts()==before
