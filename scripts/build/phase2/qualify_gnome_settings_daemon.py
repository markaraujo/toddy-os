"""Bind exact full selected GSD build, originals and private schema consumers."""
from pathlib import Path
import hashlib,json,re

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/gnome-settings-daemon-50.1');w=Path('/mnt/lfs/sources/phase2/work/gnome-settings-daemon-1');l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','gnome-settings-daemon-build.sh'),('toddy-probe.py','gnome-settings-daemon-probe.py')]:assert (s/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert (l/'gnome-settings-daemon-1.exit').read_text().strip()=='0'
 assert json.loads((l/'gnome-settings-daemon-1.job.json').read_text())['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),str(s),str(w),'bash','/src/toddy-build.sh']
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 rows=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
 assert len(rows)==11 and all(x['result']=='OK' and x['returncode']==0 for x in rows)
 assert r['original_tests']==[{k:x[k] for k in ['name','result','returncode']} for x in rows]
 power=[x for x in rows if ':test-power ' in x['name']];assert len(power)==9
 assert sum(int(re.findall(r'Ran (\d+) tests? in ',x.get('stderr','')+'\n'+x.get('stdout',''))[0]) for x in power)==26
 assert not any(re.search(r'#\s*SKIP|^OK \(skipped=',x.get('stdout','')+'\n'+x.get('stderr',''),re.M|re.I) for x in rows)
 assert r['consumer']=={'private_schema_count':24,'typed_color_boolean_uint':True,'invalid_power_enum_refused':True,'memory_settings_reset_recovery_cycles':2,'stock_schema_cache_or_actual_services_display_audio_power_tested':False}
 assert len(r['artifacts'])==134 and len(r['stage_sha256'])==156
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 for name in ['color','power','media-keys']:assert '--help' in (w/('CLI-'+name+'-help.log')).read_text()
 return r
