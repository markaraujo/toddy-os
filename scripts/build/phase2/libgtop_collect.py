"""Qualify the existing libgtop stage with a corrected own public-header probe."""
from pathlib import Path
import hashlib,json,subprocess

def files(base,elf=False):
 return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'\x7fELF')}

def main(recipe,probe):
 w=Path('/build');assert not (w/'probe-2.c').exists() and not (w/'stage-results.json').exists()
 before={'artifacts':files(w/'compile',True),'stage_sha256':files(Path('/stage'))};assert all(before.values())
 (w/'before-collect-2.json').write_text(json.dumps(before,indent=2)+'\n')
 (w/'probe-2.c').write_text(probe)
 assert recipe.count('cc /src/toddy-probe.c')==1
 suffix=recipe[recipe.index('cc /src/toddy-probe.c'):].replace('/src/toddy-probe.c','/build/probe-2.c')
 subprocess.run(['bash','-euo','pipefail','-c',suffix],check=True)
 r=json.loads((w/'stage-results.json').read_text());assert r['artifacts']==before['artifacts'] and r['stage_sha256']==before['stage_sha256']
