"""Run the unchanged actual VTE consumer with a private PTY; preserve build/stage."""
from pathlib import Path
import hashlib,json,os,subprocess

def hashes(base,elf=False):
 return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'\x7fELF')}
def main():
 w=Path('/build');assert not (w/'stage-results.json').exists()
 assert (w/'original-tests.exit').read_text().strip()=='0'
 assert (w/'compile/meson-logs/install-log.txt').exists()
 before={'artifacts':hashes(w/'compile',True),'stage_sha256':hashes(w/'stage')}
 assert before['artifacts'] and before['stage_sha256']
 p=w/'probe-2';p.mkdir();(p/'before.json').write_text(json.dumps(before,indent=2)+'\n')
 env=os.environ.copy();env.update(LD_LIBRARY_PATH='/stage/usr/lib',GI_TYPELIB_PATH='/stage/usr/lib/girepository-1.0')
 with (p/'consumer.json').open('x') as out:
  r=subprocess.run(['/build/native-probe','/stage/etc/profile.d/vte.sh'],env=env,stdout=out,timeout=70)
 (p/'consumer.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
 code="import gi,json;gi.require_version('Vte','2.91');from gi.repository import Vte;assert (Vte.get_major_version(),Vte.get_minor_version(),Vte.get_micro_version())==(0,84,1);print(json.dumps({'namespace':'Vte2.91','runtime_version':'0.84.1','widget_or_display_tested':False}))"
 gi=json.loads(subprocess.check_output(['python3','-c',code],env=env,text=True,timeout=15))
 assert hashes(w/'compile',True)==before['artifacts'] and hashes(w/'stage')==before['stage_sha256']
 rows=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
 assert rows and all(r['result'] in ['OK','SKIP','EXPECTEDFAIL'] for r in rows)
 result={'scope':'VTE0.84.1 GTK3/API2.91. Original compile/tests/stage retained. Actual regex/PTY/geometry/UTF8/managed-group Stop/fresh recovery/interactive owner prompt/GI. No widget/GNOME Terminal/graphical focus acceptance. Private devpts replaces missing test device only.','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'consumer':json.loads((p/'consumer.json').read_text()),'GI_consumer':gi,'shell_integration':json.loads((w/'shell-integration-selection.json').read_text()),'probe_only_recovery':{'compile_and_stage_unchanged':True,'original_failure_retained':True,'private_devpts':True},**before}
 (w/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
