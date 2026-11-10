"""Bind real metadata-feature tests and independent parser refusal to exact stage."""
from pathlib import Path
import hashlib,json,re

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 l=Path('/var/log/toddy/phase2');w=Path('/mnt/lfs/sources/phase2/work/exiv2-1');s=Path('/mnt/lfs/sources/phase2/inputs/exiv2-0.28.8')
 prepared=json.loads((s/'toddy-prepared.json').read_text());assert prepared['source_sha256']=='ea51b0609f58a9afa063b60daa1539948b62247721e154f4fff0ad3aec9f9756'
 assert digest(s/'toddy-build.sh')==prepared['recipe_sha256'] and digest(s/'toddy-probe.py')==prepared['probe_sha256']
 assert (l/'exiv2-1.exit').read_text().strip()=='1' and (l/'exiv2-finish-2.exit').read_text().strip()=='1' and (l/'exiv2-features-3.exit').read_text().strip()=='1' and (l/'exiv2-features-4.exit').read_text().strip()=='1' and (l/'exiv2-probe-5.exit').read_text().strip()=='1' and (l/'exiv2-probe-7.exit').read_text().strip()=='0'
 command=json.loads((l/'exiv2-features-4.job.json').read_text())['command'];assert command[-2]==(root/'scripts/build/phase2/exiv2_features.py').read_text()
 command=json.loads((l/'exiv2-probe-7.job.json').read_text())['command'];assert command[-3:]==[(root/'scripts/build/phase2/exiv2_probe_finish.py').read_text(),(root/'scripts/build/phase2/exiv2-probe.py').read_text(),'probe-7']
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0 and r['consumer_exit']==1
 for base,key,count in [('compile','artifacts',92),('stage','stage_sha256',55)]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')};assert len(actual)==count and actual==r[key]
 rows=json.loads((w/'features-3/original-results.json').read_text());assert rows==r['original_tests'] and len(rows)==5 and all(x['exit']==0 for x in rows)
 counts={};skips=[]
 for x in rows:
  p=w/'features-3'/(x['name']+'.log');assert digest(p)==x['log_sha256'];text=p.read_text();n=re.findall(r'^Ran (\d+) tests? in ',text,re.M);assert len(n)==1 and not re.search(r'^FAILED',text,re.M)
  counts[x['name']]=int(n[0]);skips += [{'driver':x['name'],'detail':line} for line in text.splitlines() if '... skipped ' in line]
 assert counts=={'bugfixTests':310,'lensTests':532,'tiffTests':1,'versionTests':0,'regressionTests':326} and len(skips)==10 and all(x['driver']=='bugfixTests' for x in skips)
 cache=(w/'compile/CMakeCache.txt').read_text()
 for option,value in [('EXIV2_ENABLE_BROTLI','ON'),('EXIV2_ENABLE_INIH','ON'),('EXIV2_ENABLE_XMP','ON'),('EXIV2_ENABLE_PNG','ON'),('EXIV2_ENABLE_BMFF','ON'),('EXIV2_ENABLE_VIDEO','ON'),('EXIV2_ENABLE_WEBREADY','OFF'),('EXIV2_ENABLE_CURL','OFF'),('EXIV2_BUILD_SAMPLES','OFF')]:assert re.search(r'^'+option+':BOOL='+value+'$',cache,re.M)
 assert digest(s/'src/canonmn_int.cpp')==r['readonly_canon_source_sha256']
 legacy=json.loads((w/'features-3/legacy-profile.json').read_text())
 for name in ['bin/exiv2','lib/libexiv2.so.0.28.8']:assert digest(w/'features-3/legacy-binaries'/name)==legacy['ELFs'][name]
 p=json.loads((w/'probe-7/result.json').read_text());assert p['consumer_exit']==0 and p['all_compiled_and_stage_hashes_unchanged']
 assert p['consumer']=={'local_PNG_EXIF_UTF8_edit_read_reset_cycles':2,'IDAT_IHDR_IEND_unchanged':True,'corrupt_JPEG_refusals':2,'failed_input_unchanged':True,'recovery_cycles':2,'valid_XMP_parser_control':True,'external_entity_refused_canary_not_read':True,'XMP_recovery':True,'remote_transport_or_GUI_tested':False}
 return {'stage':r,'consumer':p['consumer'],'original_driver_counts':counts,'original_skips':skips}
