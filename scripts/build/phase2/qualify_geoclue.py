"""Bind the real full-backend build and typed client ABI without fake tests."""
from pathlib import Path
import hashlib,json
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/geoclue-2.8.2');w=Path('/mnt/lfs/sources/phase2/work/geoclue-1');l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','geoclue-build.sh'),('toddy-probe.c','geoclue-probe.c')]:assert (s/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert (l/'geoclue-1.exit').read_text().strip()=='0'
 assert json.loads((l/'geoclue-1.job.json').read_text())['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),str(s),str(w),'bash','/src/toddy-build.sh']
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert r['original_registered_tests']==json.loads((w/'original-registered-tests.json').read_text())==[]
 assert r['consumer']=={'actual_GObject_DBUS_skeletons':True,'UTF8_typed_properties':True,'wrong_variant_lookup_refused':True,'typed_property_recovery_cycles':2,'actual_service_authorization_or_owner_position_tested':False}
 assert r['daemon_version']=='2.8.2' and r['daemon_invalid_option_refused']
 config=(w/'compile/config.h').read_text()
 for flag in ['WIFI','STATIC','IP','COMPASS']:assert '#define GCLUE_USE_'+flag+'_SOURCE 1' in config if flag!='COMPASS' else '#define GCLUE_USE_COMPASS 1' in config
 for flag in ['3G','CDMA','MODEM_GPS','NMEA']:assert '#define GCLUE_USE_'+flag+'_SOURCE 0' in config
 assert (w/'stage/usr/lib/systemd/system/geoclue.service').is_file() and 'User=geoclue' in (w/'stage/usr/lib/systemd/system/geoclue.service').read_text()
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 for filename,column in [('passwd',2),('group',2)]:
  rows=[s.split(':') for s in Path('/mnt/lfs/etc',filename).read_text().splitlines()]
  assert not any(t[0]=='geoclue' or t[column]=='30' for t in rows),'Reconcile existing service account/ID; no replay'
 return r
