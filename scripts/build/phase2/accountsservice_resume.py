"""Resume only known failed setup after owned JSON-C, preserving tarball copy."""
from pathlib import Path
import hashlib,json,os,subprocess
assert os.getuid()==101
source=Path('/src');private=Path('/build/source/accountsservice-26.27.3');work=Path('/build')
assert private.is_dir() and not (work/'stage-results.json').exists()
assert not (work/'compile/meson-private/coredata.dat').exists() and not (work/'compile/build.ninja').exists()
assert not list((work/'stage').iterdir())
assert subprocess.check_output(['pkg-config','--modversion','json-c'],text=True).strip()=='0.19'
def inventory(base):
 return {str(p.relative_to(base)):(('link',str(p.readlink())) if p.is_symlink() else ('sha256',hashlib.sha256(p.read_bytes()).hexdigest())) for p in base.rglob('*') if p.is_symlink() or p.is_file()}
before=inventory(source);assert inventory(private)==before
old=work/'compile/meson-logs/meson-log.txt';copy=work/'configure-json-c-failure-1.log';assert not copy.exists() and 'Dependency "json-c" not found' in old.read_text();copy.write_bytes(old.read_bytes())
recipe=(source/'toddy-build.sh').read_text();marker='cd /build/source/accountsservice-26.27.3\n';assert recipe.count(marker)==1
(work/'known-setup-resumption-2.json').write_text(json.dumps({'scope':'Fresh setup over known failed, no complete coredata/build.ninja, after actual new JSON-C dependency; original source copy preserved','original_private_copy_files_unchanged':len(before),'recipe_sha256':hashlib.sha256(recipe.encode()).hexdigest(),'missing_dependency':'json-c0.19 now owned'},indent=2)+'\n')
subprocess.run(['bash','-c','set -euo pipefail\nexport PYTHONDONTWRITEBYTECODE=1\n'+recipe[recipe.index(marker):]],check=True)
assert inventory(source)==before
