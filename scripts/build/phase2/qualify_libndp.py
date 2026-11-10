"""Bind unchanged isolated libndp source, recipe, stage and actual API evidence."""
from pathlib import Path
import hashlib,json

def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/libndp-1.9');w=Path('/mnt/lfs/sources/phase2/work/libndp-1');l=Path('/var/log/toddy/phase2')
 for a,b in [('toddy-build.sh','libndp-build.sh'),('toddy-probe.c','libndp-probe.c')]:assert (s/a).read_bytes()==(root/'scripts/build/phase2'/b).read_bytes()
 assert (l/'libndp-1.exit').read_text().strip()=='0'
 assert json.loads((l/'libndp-1.job.json').read_text())['command']==['/bin/bash',str(root/'scripts/build/phase2/isolated.sh'),str(s),str(w),'bash','/src/toddy-build.sh']
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==r['make_check_exit']==0
 assert r['original_test_suite']=='absent in frozen source/book; no test pass claimed'
 assert r['consumer']=={'message_types':5,'cycles':2,'wildcard_creation_refused':True,'payload_length_clamp_and_recovery':True,'actual_NDP_packets_sent':False}
 assert len(r['artifacts'])==4 and len(r['stage_sha256'])==6
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in r[key].items():
   with (w/base/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha
 return r
