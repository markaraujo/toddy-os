"""Only correct the own type probe; never recompile/restage accepted Shell."""
from pathlib import Path
import hashlib,json,os,subprocess

def hashes(base,elf=False):
 return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink() and (not elf or p.open('rb').read(4)==b'\x7fELF')}
def main(probe):
 w=Path('/build');assert not (w/'stage-results.json').exists()
 assert (w/'shell-version.log').read_text().strip()=='GNOME Shell 50.4'
 assert json.loads((w/'original-registered-tests.json').read_text())==[]
 assert (w/'compile/meson-logs/install-log.txt').exists()
 before={'artifacts':hashes(w/'compile',True),'stage_sha256':hashes(w/'stage')}
 assert before['artifacts'] and before['stage_sha256']
 p=w/'probe-2';p.mkdir();(p/'probe.py').write_text(probe)
 env=os.environ.copy();env.update(LD_LIBRARY_PATH='/stage/usr/lib/gnome-shell:/usr/lib/mutter-18',GI_TYPELIB_PATH='/stage/usr/lib/gnome-shell:/usr/lib/mutter-18')
 with (p/'consumer.json').open('x') as out:
  r=subprocess.run(['python3',str(p/'probe.py'),'/src','/stage',str(p)],env=env,stdout=out)
 (p/'consumer.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
 assert hashes(w/'compile',True)==before['artifacts'] and hashes(w/'stage')==before['stage_sha256']
 result={'scope':'Frozen minimal Wayland/Systemd/NM/PipeWire camera. Extensions management tools/apps and WebKit captive portal helper optional omitted. Actual CLI/GI/source JS and private schema checks only; upstream display suite/native graphical login/input/accessibility still pending. Own initial type/range API probe failure retained.','compile_exit':0,'stage_exit':0,'original_tests':[],'original_suite_pending':True,'consumer':json.loads((p/'consumer.json').read_text()),'version':(w/'shell-version.log').read_text().strip(),'probe_only_recovery':{'compile_and_stage_unchanged':True,'corrected_probe_sha256':hashlib.sha256(probe.encode()).hexdigest(),'original_failure_retained':True},**before}
 (w/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
