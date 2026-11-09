"""Compose measured original JSON-C outcomes and require unchanged actual stage."""
import hashlib,json,re,subprocess
from pathlib import Path

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 source=Path('/mnt/lfs/sources/phase2/inputs/json-c-0.19');work=Path('/mnt/lfs/sources/phase2/work/json-c-1');log=Path('/var/log/toddy/phase2')
 assert (source/'toddy-probe.c').read_bytes()==(root/'scripts/build/phase2/json-c-probe.c').read_bytes()
 proof=json.loads((work/'stage-results.json').read_text());assert proof['compile_exit']==proof['stage_exit']==0 and proof['original_programs']==28
 if (log/'json-c-finish-3.exit').exists():
  assert (log/'json-c-1.exit').read_text().strip()=='8' and (log/'json-c-cli-2.exit').read_text().strip()=='1' and (log/'json-c-finish-3.exit').read_text().strip()=='0'
  assert digest(source/'toddy-build.sh')=='93ffdc5e23b04aac8dabb0a90710246240269b725be6e232414b7cd7e1881f44'
  for job,script in [('json-c-cli-2','json_c_recover.py'),('json-c-finish-3','json_c_finish.py')]:
   r=json.loads((log/(job+'.job.json')).read_text());assert r['command'][2:]==[str(source),str(work),'python3','-c',(root/'scripts/build/phase2'/script).read_text()]
  assert proof['reused_original_programs']==27 and proof['corrected_original_programs']==1
  old=(work/'original-tests.log').read_text();passed=set(re.findall(r'Test\s+#\d+:\s+(\S+)\s+[^\n]*Passed',old));assert len(passed)==27
  # The exact successful finish producer verified LastTest before CTest's
  # show-only inventory replaced that mutable bookkeeping file. Reuse its
  # bound exit0 plus immutable per-run CLI result; never replay the test.
  cli=(work/'cli-only-tests.log').read_text();assert '100% tests passed out of 1' in cli and re.search(r'Test\s+#1:\s+test_json_parse_cli\s+[^\n]*Passed',cli)
  for name,sha in proof['unchanged_original_elfs'].items():assert digest(work/'compile'/name)==sha
 else:
  assert (log/'json-c-1.exit').read_text().strip()=='0'
  assert (source/'toddy-build.sh').read_bytes()==(root/'scripts/build/phase2/json-c-build.sh').read_bytes()
  assert proof['original_tests_exit']==0 and '100% tests passed' in (work/'original-tests.log').read_text()
 consumer=proof['consumer'];assert consumer['version']=='0.19'
 assert all(consumer[k] for k in ['typed_identity','unicode','false_permission_preserved','malformed_refused','invalid_utf8_refused','depth_bound_refused','recovery'])
 for name,sha in proof['stage_sha256'].items():assert digest(work/'stage'/name)==sha
 assert set(proof['stage_sha256'])=={str(p.relative_to(work/'stage')) for p in (work/'stage').rglob('*') if p.is_file() and not p.is_symlink()}
 assert not (work/'stage/usr/bin/json_parse').exists()
