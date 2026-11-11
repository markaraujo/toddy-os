"""Record actual isolated portal build/stage and selected security features."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
name,version,binary=sys.argv[1:];assert os.getuid()==101
w=Path('/build');s=Path('/stage');target=s/binary;assert target.is_file() and target.read_bytes()[:4]==b'\x7fELF'
options={r['name']:r['value'] for r in json.loads((w/'compile/meson-info/intro-buildoptions.json').read_text())}
if name=='xdg-desktop-portal':
 for key in ['sandboxed-image-validation','sandboxed-sound-validation','systemd']:assert options[key]=='enabled',(key,options[key])
 assert options['tests']=='disabled' and options['flatpak-interfaces']=='disabled'
 r=subprocess.run([str(target),'--version'],capture_output=True,text=True,timeout=15);assert r.returncode==0 and version in r.stdout,(r.stdout,r.stderr)
 version_result={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
else:version_result=None
files={}
for p in s.rglob('*'):
 if not p.is_symlink():assert not p.stat().st_mode&0o6000,p
 if p.is_file() and not p.is_symlink():files[str(p.relative_to(s))]=hashlib.sha256(p.read_bytes()).hexdigest()
result={'scope':'Isolated native compiler/stage and exact selected features only. Optional upstream integration suite not run per frozen-book build profile. Actual portal session/consent/cancel/denial/appearance tests remain required.','name':name,'version':version,'compile_exit':0,'stage_exit':0,'selected_build_options':options,'version_cli':version_result,'upstream_tests_passed':0,'upstream_test_status':'Not run; selected frozen-book build profile','stage_sha256':files,'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'}}
assert os.statvfs(w).f_bavail*os.statvfs(w).f_frsize>=16*1024**3
(w/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['stage_sha256','artifacts','selected_build_options']}))
