"""Run only corrected own consumers/collection on the unchanged original stage."""
from pathlib import Path
import hashlib,json,subprocess

def main(recipe,probe):
 w=Path('/build');assert not (w/'probe-3.c').exists() and not (w/'stage-results.json').exists()
 before=json.loads((w/'before-finish-2.json').read_text())
 actual={str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'}
 assert actual==before
 stage={str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()};assert stage
 (w/'before-collect-3-stage.json').write_text(json.dumps(stage,indent=2)+'\n')
 (w/'probe-3.c').write_text(probe)
 for pc in ['colord-gtk','colord-gtk4']:
  version=subprocess.check_output(['pkg-config','--modversion',pc],env={'PATH':'/usr/bin','PKG_CONFIG_PATH':'/stage/usr/lib/pkgconfig'},text=True);assert version.strip()=='0.3.1'
 assert recipe.count('for pc in colord-gtk colord-gtk4; do')==1
 suffix=recipe[recipe.index('for pc in colord-gtk colord-gtk4; do'):].replace('/src/toddy-probe.c','/build/probe-3.c')
 subprocess.run(['bash','-euo','pipefail','-c',suffix],check=True)
 r=json.loads((w/'stage-results.json').read_text());assert r['artifacts']==before and r['stage_sha256']==stage
