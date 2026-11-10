"""Bind companion promotion to exact real native conversion proof and unchanged core."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 l=Path('/var/log/toddy/phase2');w=Path('/mnt/lfs/sources/phase2/work/glycin-gtk4-1')
 assert (l/'glycin-gtk4-1.exit').read_text().strip()=='0'
 recipe=(root/'scripts/build/phase2/glycin_gtk4_build.py').read_text();assert json.loads((l/'glycin-gtk4-1.job.json').read_text())['command'][-1]==recipe+'\nmain()\n'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==r['GI_symbol_exit']==0 and not r['package_promotable']
 for base,key,count in [('compile','artifacts',78),('stage','stage_sha256',5)]:
  assert len(r[key])==count
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 proof=json.loads((l/'glycin-gtk4-native-qualification.json').read_text());report=json.loads((l/'glycin-gtk4-native-runtime-1.json').read_text())
 assert proof['state']=='native-companion-conversion-qualified' and proof['container_exit']==0 and proof['OOMKilled'] is False and proof['backing_unchanged']
 assert hashlib.sha256(json.dumps(report,sort_keys=True).encode()).hexdigest()==proof['report_sha256']
 assert report['kernel']=='7.1.8-toddy' and report['pid1']=='systemd' and len(report['runs'])==1 and report['runs'][0]['exit']==0
 expected={'sandbox':'BWRAP','installed_default_loader_paths':True,'source_image_pixel_cases':4,'GDK_texture_PNG_pixel_roundtrips':4,'malformed_refusals':2,'recovery_cycles':2,'display_or_widgets_tested':False}
 assert json.loads(report['runs'][0]['stdout'])==proof['consumer']==expected
 assert report['stage_file_hashes']==proof['stage_sha256']==r['stage_sha256']
 assert report['installed_core_files_unchanged']==proof['installed_core_sha256']
 for name,sha in proof['installed_core_sha256'].items():assert digest(Path('/mnt/lfs')/name.lstrip('/'))==sha
 source=Path('/mnt/lfs/sources/phase2/inputs/glycin-2.1.5')
 assert digest(source/'project/Cargo.lock')==r['cargo_lock_sha256']=='5ff1ad293efde5c927f19df0f488dc80a04814367dbc480a3cc45847646bc669'
 return proof
