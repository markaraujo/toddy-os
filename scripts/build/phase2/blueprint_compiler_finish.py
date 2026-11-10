"""Reconcile the original linter fixture access; never replay approved tests/build."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess

def hashes(base):
 return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink()}
def main():
 assert os.getuid()==101
 w=Path('/build');source=Path('/src');old=(w/'original-selected-tests.log').read_text()
 passed=re.findall(r'^(test_\w+ \([^)]+\)) \.\.\. ok$',old,re.M);assert len(passed)==4
 assert 'Ran 5 tests' in old and 'FAILED (errors=15)' in old and old.count('PermissionError:')==15
 assert not list(Path('/stage').iterdir())
 generated={name:hashlib.sha256((w/'compile'/name).read_bytes()).hexdigest() for name in ['config.py','blueprint-compiler','blueprint-compiler.pc','docs/reference_docs.json']}
 before=hashes(source/'tests');private=w/'private-tests-2';private.mkdir();shutil.copytree(source/'tests',private/'tests',symlinks=True);assert hashes(private/'tests')==before
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH='/src',GSETTINGS_BACKEND='memory')
 with (w/'original-linter-2.log').open('xb') as log:r=subprocess.run(['python3','-B','-m','unittest','-v','tests.test_linter'],cwd=private,env=env,stdout=log,stderr=subprocess.STDOUT)
 (w/'original-linter-2.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
 log=(w/'original-linter-2.log').read_text();assert 'Ran 1 test' in log and re.search(r'^OK$',log,re.M) and len(re.findall(r'^assert_linter\(',log,re.M))==15
 assert hashes(source/'tests')==hashes(private/'tests')==before
 with (w/'stage-2.log').open('xb') as log:r=subprocess.run(['meson','install','-C',str(w/'compile'),'--no-rebuild','--destdir','/stage'],env=env,stdout=log,stderr=subprocess.STDOUT)
 (w/'stage-2.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
 env['PYTHONPATH']='/stage/usr/lib/python3.14/site-packages'
 with (w/'native-consumer-2.json').open('xb') as out:r=subprocess.run(['python3','/src/toddy-probe.py','/stage/usr/bin/blueprint-compiler'],env=env,stdout=out)
 assert r.returncode==0
 assert all(hashlib.sha256((w/'compile'/name).read_bytes()).hexdigest()==sha for name,sha in generated.items()) and hashes(source/'tests')==before
 r={'scope':'Frozen blueprint compiler0.22.2 build-only SDK; original four tokenizer/formatter passes reused, original linter method/15fixtures passed on byte-identical private copy. Original failed read-only attempt preserved; source/private bytes unchanged. Generated build outputs unchanged, no Ninja/test replay. Full Gtk.Builder/deprecation suite deferred, no widgets/GNOME acceptance.','compile_exit':0,'stage_exit':0,'original_selected_test_cases':5,'original_linter_subcases':15,'reused_original_cases':passed,'generated_sha256':generated,'source_test_fixture_files':len(before),'source_and_private_fixture_manifest_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),'deferred':['tests.test_samples','tests.test_deprecations'],'consumer':json.loads((w/'native-consumer-2.json').read_text()),'stage_sha256':hashes(Path('/stage'))}
 (w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='stage_sha256'}))
