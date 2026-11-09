"""Repeat only original machine-ID case with synthetic namespace identity."""
from pathlib import Path
import hashlib,json,shutil,subprocess
p=Path('/build');source=p/'source';saved=p/'original-before-5';assert not saved.exists() and not (p/'stage.log').exists()
assert Path('/etc/machine-id').read_text().strip()=='00000000000000000000000000000001'
saved.mkdir()
for f in (source/'src/tests').iterdir():
 if f.suffix in ['.log','.trs']:shutil.copy2(f,saved/f.name)
def artifacts():
 return {str(f.relative_to(source)):hashlib.sha256(f.read_bytes()).hexdigest() for f in source.rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
before=artifacts();(p/'artifacts-before-5.json').write_text(json.dumps(before,indent=2)+'\n')
with (p/'original-share-5.log').open('xb') as log:subprocess.run(['make','-C',str(source/'src/tests'),'check','TESTS=ibus-share'],stdout=log,stderr=subprocess.STDOUT,check=True)
assert artifacts()==before
with (p/'original-bus-5.log').open('xb') as log:subprocess.run(['make','-C',str(source/'bus'),'check','TESTS=test-matchrule'],stdout=log,stderr=subprocess.STDOUT,check=True)
assert all(artifacts().get(n)==h for n,h in before.items())
recipe=Path('/src/toddy-build.sh').read_text();marker='make DESTDIR=/stage install > /build/stage.log 2>&1\n';assert recipe.count(marker)==1
script='set -euo pipefail\nexport PYTHONDONTWRITEBYTECODE=1\ncd /build/source\n'+marker+recipe.split(marker)[1]
subprocess.run(['bash','-c',script],check=True)
assert all(artifacts().get(n)==h for n,h in before.items())
