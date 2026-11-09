"""One unchanged original startup case with log preservation before cleanup."""
from pathlib import Path
import hashlib,json,os,runpy,unittest
assert os.getuid()==101
work=Path('/build');assert not (work/'daemon-startup-diagnostic.log').exists()
rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
failed=[r for r in rows if r['result']!='OK'];assert len(rows)==18 and len(failed)==4
registered=json.loads((work/'compile/meson-info/intro-tests.json').read_text())
row,=[r for r in registered if r['name']=='Tests.test_startup']
os.environ.update(row['env']);os.environ['PYTHONDONTWRITEBYTECODE']='1'
source=Path('/build/source/accountsservice-26.27.3/tests/test-daemon.py')
namespace=runpy.run_path(str(source),run_name='accountsservice_startup_diagnosis');Tests=namespace['Tests'];stop=Tests.stop_daemon
snapshot={}
for f in (work/'compile').rglob('*'):
 if f.is_file() and not f.is_symlink():
  with f.open('rb') as stream:
   if stream.read(4)==b'\x7fELF':stream.seek(0);snapshot[str(f.relative_to(work/'compile'))]=hashlib.file_digest(stream,'sha256').hexdigest()
(work/'original-elfs-before-diagnosis-3.json').write_text(json.dumps(snapshot,indent=2)+'\n')
def preserve(self):
 if self.log:
  data=Path(self.log.name).read_bytes();out=work/'daemon-startup-diagnostic.log'
  with out.open('xb') as f:os.fchmod(f.fileno(),0o600);f.write(data)
  (work/'daemon-startup-diagnostic-state.json').write_text(json.dumps({'daemon_exit_at_cleanup':self.daemon.poll() if self.daemon else None,'original_case':'Tests.test_startup','original_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'log_sha256':hashlib.sha256(data).hexdigest(),'scope':'Diagnostic logging only, original test assertions unchanged; no account/privilege acceptance'},indent=2)+'\n')
 stop(self)
Tests.stop_daemon=preserve
result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([Tests('test_startup')]))
for name,sha in snapshot.items():assert hashlib.sha256((work/'compile'/name).read_bytes()).hexdigest()==sha
raise SystemExit(0 if result.wasSuccessful() else 1)
