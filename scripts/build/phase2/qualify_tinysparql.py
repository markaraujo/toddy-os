"""Bind production/debug/stage hashes and four exact retained lexical failures."""
from pathlib import Path
import hashlib,json,re

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/tinysparql-3.11.1');w=Path('/mnt/lfs/sources/phase2/work/tinysparql-1');l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','tinysparql-build.sh'),('toddy-probe.c','tinysparql-probe.c')]:assert (s/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert json.loads((s/'toddy-prepared.json').read_text())['source_sha256']=='cfd46021ee1514ad435e714f7aa1ec7a787c7f516a94f4c7438897ee3d6eca1e'
 assert (l/'tinysparql-1.exit').read_text().strip()=='1'
 for job,code in [('tinysparql-sparql-census-4','tinysparql_sparql_census.py'),('tinysparql-numeric-5','tinysparql_numeric.py')]:
  assert (l/(job+'.exit')).read_text().strip()=='0'
  command=json.loads((l/(job+'.job.json')).read_text())['command']
  expected=(root/'scripts/build/phase2'/code).read_text()
  expected+= '\nmain()\n' if 'census' in job else '\nmain('+repr((root/'scripts/build/phase2/tinysparql-numeric-probe.c').read_text())+')\n'
  assert command[-1]==expected
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0 and r['original_tests_exit']==1
 rows=[json.loads(x) for x in (w/'test-compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
 assert len(rows)==30 and sum(x['result']=='OK' and x['returncode']==0 for x in rows)==29
 assert [x['name'] for x in rows if x['result']!='OK']==['core+slow - tinysparql:sparql']
 assert r['original_tests']==[{k:x[k] for k in ['name','result','returncode']} for x in rows]
 assert len(r['original_functional_tests_pending'])==17
 for base,key,count,elf in [('compile','artifacts',156,True),('test-compile','test_artifacts',207,True),('stage','stage_sha256',105,False)]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'\x7fELF')}
  assert len(actual)==count and actual==r[key]
 c=json.loads((w/'sparql-census-4/result.json').read_text());assert c['state']=='complete-with-failures' and c['all_compiled_and_stage_hashes_unchanged']
 assert len(c['results'])==len({x['case'] for x in c['results']})==491
 expected={
 '/core/sparql/aggregates/aggregate-1':'-"9"\t"3.33333333333333"\t"5"\t"1" +"9"\t"3.3333333333333335"\t"5"\t"1"',
 '/core/sparql/aggregates/aggregate-distinct-1':'-"3.33333333333333"\t"4.0" +"3.3333333333333335"\t"4.0"',
 '/core/sparql/bind/bind3':'-"http://example.org/ns#a2"\t"42"\t"0.0238095238095238" -"http://example.org/ns#e"\t"17"\t"0.0588235294117647" +"http://example.org/ns#a2"\t"42"\t"0.023809523809523808" +"http://example.org/ns#e"\t"17"\t"0.058823529411764705"',
 '/core/sparql/update/delete-where-query-3':'-"http://example/b"\t"0.444444444444444" +"http://example/b"\t"0.44444444444444442"'}
 assert {x['case'] for x in c['failures']}==set(expected)
 for x in c['results']:
  p=w/'sparql-census-4'/x['log'];assert digest(p)==x['log_sha256'];text=p.read_text()
  if x['case'] in expected:
   assert x['exit']==-6
   lines=[line for line in text.splitlines() if 'Tracker-FATAL-ERROR: --- ' in line];assert len(lines)==1
   assert lines[0].rsplit(' @@ ',1)[1]==expected[x['case']]
  else:assert x['exit']==0 and re.search(r'^1\.\.1$',text,re.M) and not re.search(r'\b(?:SKIP|TODO)\b',text)
 n=json.loads((w/'numeric-5/result.json').read_text());assert n['typed_double_arithmetic_cases']==n['lossless_text_roundtrip_cases']==4 and n['SQLite_settings_changed'] is False and n['all_compiled_and_stage_hashes_unchanged']
 assert (w/'numeric-5/probe.c').read_bytes()==(root/'scripts/build/phase2/tinysparql-numeric-probe.c').read_bytes()
 assert r['consumer']=={'UTF8_insert_query':True,'persisted_after_connection_reopen':True,'malformed_query_refused_state_preserved':True,'delete_reset_cycles':2,'desktop_indexer_GUI_or_cancellation_tested':False}
 return {'original_programs_passed':29,'core_cases_passed':487,'original_lexical_failures_retained':4,'functional_programs_deferred':17,'independent_numeric':n,'production_and_stage_unchanged':True}
