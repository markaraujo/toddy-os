"""Collect an already-built LocalSearch stage; never compile/test/install again."""
from pathlib import Path
import hashlib,json
p=Path('/build')
assert not (p/'stage-results.json').exists()
assert hashlib.sha256(Path('/src/toddy-build.sh').read_bytes()).hexdigest()=='f25eb13e03a5b1fde6763e0bea50e923bec82ebae12cbc596d0cbb2e060d2499'
def hashes():
 return {str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for base in ['compile','stage'] for f in (p/base).rglob('*') if f.is_file() and not f.is_symlink()}
before=hashes()
from pathlib import Path
import hashlib,json,os
p=Path('/build');rows=[json.loads(x) for x in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
assert len(rows)==13 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
assert (p/'cli-version.txt').read_text().startswith('LocalSearch 3.11.1\n')
config=(p/'compile/config-miners.h').read_text()
assert '#define HAVE_LANDLOCK' in config.splitlines() and '#define HAVE_LIBSECCOMP' in config.splitlines()
registered=json.loads((p/'original-registered-tests.json').read_text());ran={r['name'] for r in rows}
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=16*1024**3
r={'scope':'Frozen LocalSearch3.11.1 core miner/extractor/writeback with ICU/UPower/owned media metadata dependencies. Landlock explicitly enabled using upstream isolated distribution-build option; seccomp retained. Production release and original functional/sandbox programs compiled. Only13 non-slow common/indexer/extract utility programs executed on builder kernel; native functional/index/search/sandbox/cancellation/recovery and GUI acceptance remain pending. Optional absent format libraries remain auto-unavailable; man generation omitted because a2x is absent. No installed runtime or general parser-security claim.','compile_exit':0,'stage_exit':0,'kernel':os.uname().release,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'registered_not_executed':[r['name'] for r in registered if not any(s.split(':',1)[-1]+' - localsearch:'+r['name'] in ran for s in r['suite'])],'resource':json.loads((p/'compile-resource.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to('/stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in Path('/stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
assert hashes()==before, 'Collection changed original compiled/staged bytes'
