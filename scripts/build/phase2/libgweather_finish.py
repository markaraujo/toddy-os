"""Preserve the external METAR failure and resume only stage/offline consumer."""
from pathlib import Path
import hashlib,json,subprocess,sys
p=Path('/build');assert not (p/'stage-results.json').exists() and not any((p/'stage').iterdir())
tests=[json.loads(t) for t in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if t.strip()]
assert len(tests)==4
core=[t for t in tests if t['name']!='libgweather:metar'];external=[t for t in tests if t['name']=='libgweather:metar']
assert len(core)==3 and all(t['result']=='OK' and t['returncode']==0 for t in core)
assert len(external)==1 and external[0]['result']=='ERROR' and external[0]['returncode']==-6
assert 'aviationweather.gov' in (p/'original-tests.log').read_text()
before={str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
(p/'ELFs-before-stage-2.json').write_text(json.dumps(before,indent=2)+'\n')
body=sys.argv[1];marker='meson install -C /build/compile --destdir /stage --no-rebuild\n';assert body.count(marker)==1
script='set -euo pipefail\nexport PYTHONDONTWRITEBYTECODE=1 GSETTINGS_BACKEND=memory\n'+marker+body.split(marker)[1]
subprocess.run(['bash','-c',script],check=True)
assert all(hashlib.sha256((p/'compile'/name).read_bytes()).hexdigest()==sha for name,sha in before.items())
