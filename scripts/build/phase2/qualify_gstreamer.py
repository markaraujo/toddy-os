"""Exact native GStreamer core originals/stage/consumer bindings."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/gstreamer-1.28.6');w=Path('/mnt/lfs/sources/phase2/work/gstreamer-1');l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','gstreamer-build.sh'),('toddy-probe.py','gstreamer-probe.py')]:assert (s/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert json.loads((s/'toddy-prepared.json').read_text())['source_sha256']=='62b6b9f0ad3147a6dd6420ac64a91180b14e990695bddd353b96041611d052ca'
 assert (l/'gstreamer-1.exit').read_text().strip()=='0'
 assert json.loads((l/'gstreamer-1.job.json').read_text())['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),'--loopback',str(s),str(w),'bash','/src/toddy-build.sh']
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert (w/'original-tests.exit').read_text().strip()=='0'
 rows=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
 assert len(rows)==108 and sum(x['result']=='OK' and x['returncode']==0 for x in rows)==107
 skipped=[x for x in rows if x['result']=='SKIP'];assert len(skipped)==1 and skipped[0]['name']=='gstreamer:validate.simplest' and 'not available' in skipped[0]['stdout']
 assert r['original_tests']==[{k:x[k] for k in ['name','result','returncode']} for x in rows]
 assert len(r['artifacts'])==406 and len(r['stage_sha256'])==213
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 c=r['consumer'];assert c['version']=='1.28.6' and c['typed_caps_and_buffer'] and c['missing_element_refused']
 assert len(c['synthetic_pipeline_cycles'])==2 and all(x['EOS_received'] and x['stop_NULL_verified'] for x in c['synthetic_pipeline_cycles'])
 assert not c['hardware_audio_video_screencast_tested']
 assert not any('ptp-helper' in n for n in r['stage_sha256'])
 return r
