"""Bind qualified GExiv2 source/build/original programs and corrected own probe."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/gexiv2-0.16.2');w=Path('/mnt/lfs/sources/phase2/work/gexiv2-1');l=Path('/var/log/toddy/phase2')
 assert json.loads((s/'toddy-prepared.json').read_text())['source_sha256']=='aad9e240fdffbe85e390f46ee0a567e251baea5c29c3d8690260388683dc8d0a'
 assert (s/'toddy-build.sh').read_bytes()==(root/'scripts/build/phase2/gexiv2-build.sh').read_bytes()
 old=(s/'toddy-probe.py').read_text();new=(root/'scripts/build/phase2/gexiv2-probe.py').read_text()
 if (l/'gexiv2-probe-2.exit').exists():
  assert (l/'gexiv2-1.exit').read_text().strip()=='1' and (l/'gexiv2-probe-2.exit').read_text().strip()=='0'
  assert old.replace('r.try_get_tag_string(key)==value','r.try_get_tag_string(key)==\'lang="x-default" \'+value')==new
  assert json.loads((l/'gexiv2-probe-2.job.json').read_text())['command'][-1]==(root/'scripts/build/phase2/gexiv2_probe_finish.py').read_text()
 else:
  assert (l/'gexiv2-1.exit').read_text().strip()=='0' and old==new
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert (w/'original-tests.exit').read_text().strip()=='0'
 rows=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
 assert {x['name'] for x in rows}=={'gexiv2:regression','gexiv2:python3-gexiv2','gexiv2:python3-metadata'} and len(rows)==3 and all(x['result']=='OK' and x['returncode']==0 for x in rows)
 assert r['original_tests']==[{k:x[k] for k in ['name','result','returncode']} for x in rows]
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')};assert actual and actual==r[key]
 assert r['consumer']=={'GI_namespace':'GExiv2-0.16','UTF8_PNG_metadata_write_read_reset_cycles':2,'image_chunks_retained':True,'malformed_JPEG_refusals':2,'inputs_unchanged_on_refusal':True,'recovery_cycles':2}
 if 'probe_sha256' in r:assert r['probe_sha256']==hashlib.sha256(new.encode()).hexdigest()
 return r
