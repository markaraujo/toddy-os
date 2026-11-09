"""Verify existing seven passes/one exact upstream skip, without any replay."""
from pathlib import Path
import hashlib,json,os
assert os.getuid()==101
work=Path('/build')
assert not (work/'stage-results.json').exists()
assert (work/'original-tests.exit').read_text().strip()=='0'
def elfs():
 result={}
 for p in (work/'compile').rglob('*'):
  if p.is_file() and not p.is_symlink():
   with p.open('rb') as f:
    if f.read(4)==b'\x7fELF':f.seek(0);result[str(p.relative_to(work))]=hashlib.file_digest(f,'sha256').hexdigest()
 return result
before=elfs();assert before
p=Path('/build');rows=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
registered=json.loads((p/'compile/meson-info/intro-tests.json').read_text());assert len(rows)==len(registered)==8
expected={'import-repeatedly','client','exception-py3','p2p','signals','standalone','unusable-main-loop','run-test.sh'}
assert {r['name'].split(':')[-1] for r in rows}==expected
for r in rows:
 if r['name'].split(':')[-1]=='import-repeatedly':
  assert r['result']=='SKIP' and r['returncode']==0 and r['stdout']=='1..1\nok 1 # SKIP https://gitlab.freedesktop.org/dbus/dbus-python/-/issues/55\n' and not r.get('stderr')
 else:assert r['result']=='OK' and r['returncode']==0
assert '#if DBUSPY_PY_VERSION_AT_LEAST(3, 12, 0, 0)' in Path('/src/test/import-repeatedly.c').read_text()
proof={'scope':'Native Python3.14 extension original eight private-bus driver programs and actual typed owner/error/name/reconnect; test dependency, not Polkit/GNOME acceptance','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'upstream_passed_programs':7,'upstream_skipped_programs':1,'unqualified':'Repeated embedded-interpreter reinitialization is explicitly skipped by upstream for Python>=3.12; not a pass. Selected test-tool profile uses one initialization per process.','native_consumer_exit':0,'consumer':json.loads((p/'native-consumer.json').read_text()),'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(proof,indent=2)+'\n')

assert before==elfs()
p=work/'stage-results.json';r=json.loads(p.read_text());r['unchanged_compiled_elfs']=before;r['no_compiler_stage_or_test_replay']=True;p.write_text(json.dumps(r,indent=2)+'\n')
