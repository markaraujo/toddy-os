"""Run only corrected GI lookup; reuse successful C and original compiled/stage."""
from pathlib import Path
import hashlib,json,os,subprocess

def hashes(base,elf=False):
 return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'\x7fELF')}
def main(code):
 w=Path('/build');assert not (w/'stage-results.json').exists()
 assert (w/'probe-2/consumer.exit').read_text().strip()=='0'
 before=json.loads((w/'probe-2/before.json').read_text())
 assert hashes(w/'compile',True)==before['artifacts'] and hashes(w/'stage')==before['stage_sha256']
 p=w/'GI-3';p.mkdir();(p/'probe.py').write_text(code)
 env=os.environ.copy();env.update(LD_LIBRARY_PATH='/stage/usr/lib',GI_TYPELIB_PATH='/stage/usr/lib/girepository-1.0')
 with (p/'consumer.json').open('x') as out:r=subprocess.run(['python3',str(p/'probe.py')],env=env,stdout=out,timeout=15)
 (p/'consumer.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
 assert hashes(w/'compile',True)==before['artifacts'] and hashes(w/'stage')==before['stage_sha256']
 rows=json.loads((w/'original-registered-tests.json').read_text());assert len(rows)==30
 result={'scope':'Frozen libhandy1.8.3 GTK3/GI/Vala. All30original graphical programs compiled/deferred, NONE executed or passed. Own C/GI non-widget UTF8/value-copy/ownership/enum/two reset cycles only. Own C destination type and non-introspectable convenience constructor assumptions corrected independently; no library/source/stage/test replay or GUI acceptance.','compile_exit':0,'stage_exit':0,'original_tests_passed':0,'original_graphical_tests_pending':[r['name'] for r in rows],'consumer':json.loads((w/'probe-2/consumer.json').read_text()),'GI_consumer':json.loads((p/'consumer.json').read_text()),'probe_only_recovery':{'compile_and_stage_unchanged':True,'original_failures_retained':True,'corrected_C_probe_sha256':hashlib.sha256((w/'probe-2/probe.c').read_bytes()).hexdigest(),'corrected_GI_probe_sha256':hashlib.sha256(code.encode()).hexdigest()},**before}
 (w/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
