"""Correct own GValue destination initialization without touching library/stage."""
from pathlib import Path
import hashlib,json,os,subprocess

def hashes(base,elf=False):
 return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'\x7fELF')}
def main(probe):
 w=Path('/build');assert not (w/'stage-results.json').exists()
 assert (w/'compile/meson-logs/install-log.txt').exists()
 rows=json.loads((w/'original-registered-tests.json').read_text());assert len(rows)==30
 before={'artifacts':hashes(w/'compile',True),'stage_sha256':hashes(w/'stage')}
 p=w/'probe-2';p.mkdir();(p/'probe.c').write_text(probe);(p/'before.json').write_text(json.dumps(before,indent=2)+'\n')
 env=os.environ.copy();env.update(LD_LIBRARY_PATH='/stage/usr/lib',GI_TYPELIB_PATH='/stage/usr/lib/girepository-1.0')
 subprocess.run(['bash','-c','cc /build/probe-2/probe.c -I/stage/usr/include/libhandy-1 -L/stage/usr/lib $(pkg-config --cflags --libs gtk+-3.0) -lhandy-1 -Wl,-rpath,/stage/usr/lib -o /build/probe-2/native-probe'],check=True,env=env)
 with (p/'consumer.json').open('x') as out:r=subprocess.run([str(p/'native-probe')],env=env,stdout=out,timeout=20)
 (p/'consumer.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
 code="import gi,json;gi.require_version('Handy','1');from gi.repository import Handy;v=Handy.ValueObject.new_string('Toddy ã');assert v.get_string()=='Toddy ã' and v.dup_string()=='Toddy ã';print(json.dumps({'namespace':'Handy1','UTF8_value_object':True,'widget_or_display_tested':False}))"
 gi=json.loads(subprocess.check_output(['python3','-c',code],env=env,text=True,timeout=15))
 assert hashes(w/'compile',True)==before['artifacts'] and hashes(w/'stage')==before['stage_sha256']
 result={'scope':'Frozen libhandy1.8.3 GTK3/GI/Vala. All30original graphical programs compiled/deferred, NONE executed or passed. Own C/GI non-widget UTF8/value-copy/ownership/enum/two reset cycles only; own missing destination type corrected probe-only, original failure retained. No widget/Terminal/display acceptance.','compile_exit':0,'stage_exit':0,'original_tests_passed':0,'original_graphical_tests_pending':[r['name'] for r in rows],'consumer':json.loads((p/'consumer.json').read_text()),'GI_consumer':gi,'probe_only_recovery':{'compile_and_stage_unchanged':True,'original_failure_retained':True,'corrected_probe_sha256':hashlib.sha256(probe.encode()).hexdigest()},**before}
 (w/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
