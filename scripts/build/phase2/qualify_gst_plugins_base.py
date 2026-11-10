"""Bind actual base portable originals and explicitly deferred real GL tests."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/gst-plugins-base-1.28.6');w=Path('/mnt/lfs/sources/phase2/work/gst-plugins-base-1');l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','gst-plugins-base-build.sh'),('toddy-probe.py','gst-plugins-base-probe.py')]:assert (s/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert json.loads((s/'toddy-prepared.json').read_text())['source_sha256']=='0ba699c7c6c66f4ba640be78cb38a24715add9683f3e3a199f5369dc5a4f04ac'
 assert (l/'gst-plugins-base-1.exit').read_text().strip()=='0'
 assert json.loads((l/'gst-plugins-base-1.job.json').read_text())['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),'--loopback',str(s),str(w),'bash','/src/toddy-build.sh']
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 rows=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
 assert len(rows)==117 and sum(x['result']=='OK' and x['returncode']==0 for x in rows)==80
 skipped=[x for x in rows if x['result']=='SKIP'];assert len(skipped)==37 and all(':validate.' in x['name'] for x in skipped)
 assert r['original_tests']==[{k:x[k] for k in ['name','result','returncode']} for x in rows]
 registered=json.loads((w/'original-registered-tests.json').read_text());deferred=r['deferred_originals']['tests']
 assert len(registered)==134 and len(deferred)==17
 assert {x['name'] for x in deferred}|{x['name'].split(':',1)[1] for x in rows}=={x['name'] for x in registered}
 assert not {x['name'] for x in deferred}&{x['name'].split(':',1)[1] for x in rows}
 assert len(r['artifacts'])==660 and len(r['stage_sha256'])==331
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():assert digest(w/base/name)==sha
 c=r['consumer'];assert c['version']=='1.28.6' and c['GstApp_Audio_Video_GI'] and c['typed_video_8x8_RGB'] and c['typed_audio_48k_stereo']
 assert len(c['synthetic_samples'])==4 and all(x['EOS_received'] and x['stop_NULL_verified'] for x in c['synthetic_samples'])
 assert not c['devices_GL_audio_playback_screencast_tested']
 return r
