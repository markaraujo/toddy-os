"""Qualify original compiler cases with retained read-only fixture failure."""
from pathlib import Path
import hashlib,json,re

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/blueprint-compiler-0.22.2');w=Path('/mnt/lfs/sources/phase2/work/blueprint-compiler-1');l=Path('/var/log/toddy/phase2')
 prepared=json.loads((s/'toddy-prepared.json').read_text());assert prepared['source_sha256']=='231d72efbac931c235ac3e022fe94982095c20d88721d9a8dcf60152f2017e07'
 old=(s/'toddy-build.sh').read_text();assert hashlib.sha256(old.encode()).hexdigest()==prepared['recipe_sha256']
 before='(cd /src; python3 -B -m unittest -v tests.test_tokenizer tests.test_formatter tests.test_linter)'
 after='mkdir /build/private-tests\ncp -a /src/tests /build/private-tests/tests\n(cd /build/private-tests; PYTHONPATH=/src python3 -B -m unittest -v tests.test_tokenizer tests.test_formatter tests.test_linter)'
 assert old.count(before)==1 and old.replace(before,after)==(root/'scripts/build/phase2/blueprint-compiler-build.sh').read_text()
 assert (s/'toddy-probe.py').read_bytes()==(root/'scripts/build/phase2/blueprint-compiler-probe.py').read_bytes()
 assert (l/'blueprint-compiler-1.exit').read_text().strip()=='1' and (l/'blueprint-compiler-finish-2.exit').read_text().strip()=='0'
 assert json.loads((l/'blueprint-compiler-finish-2.job.json').read_text())['command'][-1]==(root/'scripts/build/phase2/blueprint_compiler_finish.py').read_text()+'\nmain()\n'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0 and r['original_selected_test_cases']==5 and r['original_linter_subcases']==15
 oldlog=(w/'original-selected-tests.log').read_text();assert 'FAILED (errors=15)' in oldlog and oldlog.count('PermissionError:')==15
 assert re.findall(r'^(test_\w+ \([^)]+\)) \.\.\. ok$',oldlog,re.M)==r['reused_original_cases'] and len(r['reused_original_cases'])==4
 log=(w/'original-linter-2.log').read_text();assert 'Ran 1 test' in log and re.search(r'^OK$',log,re.M) and len(re.findall(r'^assert_linter\(',log,re.M))==15
 for name,sha in r['generated_sha256'].items():assert digest(w/'compile'/name)==sha
 for base in [s/'tests',w/'private-tests-2/tests']:
  files={str(p.relative_to(base)):digest(p) for p in base.rglob('*') if p.is_file() and not p.is_symlink()};assert len(files)==r['source_test_fixture_files']==411
  assert hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()==r['source_and_private_fixture_manifest_sha256']
 files={str(p.relative_to(w/'stage')):digest(p) for p in (w/'stage').rglob('*') if p.is_file() and not p.is_symlink()};assert files==r['stage_sha256']
 assert r['consumer']=={'UTF8_Gtk_XML_cycles':2,'invalid_property_refusals':2,'recovery_cycles':2,'widgets_or_display_tested':False}
 return r
